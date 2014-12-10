package com.paxnil.useless.ant;

import java.io.File;
import java.io.IOException;
import java.util.Collection;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Vector;

import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;

import org.apache.ivy.ant.IvyCacheTask;
import org.apache.ivy.core.IvyPatternHelper;
import org.apache.ivy.core.module.descriptor.Artifact;
import org.apache.ivy.core.report.ArtifactDownloadReport;
import org.apache.tools.ant.BuildException;
import org.apache.tools.ant.types.FileSet;
import org.apache.tools.ant.types.resources.FileResource;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class IvyEclipse extends IvyCacheTask {
    
    public static final String ECLIPSE_STANDARD_VM_PREFIX = "org.eclipse.jdt.launching.JRE_CONTAINER/"
            + "org.eclipse.jdt.internal.debug.ui.launcher.StandardVMType/";
    
    static String getArtifactKey(Artifact art) {
        return art.getAttribute(IvyPatternHelper.ORGANISATION_KEY) + "!" +
                art.getAttribute(IvyPatternHelper.MODULE_KEY) + "!" +
                art.getAttribute(IvyPatternHelper.REVISION_KEY);
    }
    
    static String relatival(File file, File base) {
        try {
            String parent = base.getCanonicalPath();
            String child = file.getCanonicalPath();
            if (child.startsWith(parent)) {
                return base.toURI().relativize(file.toURI()).toString()
                        .replaceAll("/$", "");
            } else {
                return child;
            }
        } catch (IOException e) {
            throw new BuildException(e);
        }

    }
    
    class IvyCacheEntry {
        
        String organisation;
        String module;
        String revision;
        File binary;
        File sources;
        File javadoc; 
        
        public IvyCacheEntry(ArtifactDownloadReport report) {
            Artifact artifact = report.getArtifact();
            organisation = artifact.getAttribute(IvyPatternHelper.ORGANISATION_KEY);
            module = artifact.getAttribute(IvyPatternHelper.MODULE_KEY);
            revision = artifact.getAttribute(IvyPatternHelper.REVISION_KEY);
        }
        
        void merge(ArtifactDownloadReport report) {
            String type = report.getType();
            if(type.equals("jar")) {
                binary = report.getLocalFile();
            } else if (type.equals("source")) {
                sources = report.getLocalFile();
            } else if (type.equals("javadoc")) {
                javadoc = report.getLocalFile();
            }
        }
    }
    
    public static class SourceFolderEntry {
        
        String dir;
        String includes;
        String excludes;
        
        public void setDir(String dir) {
            this.dir = dir;
        }
        public void setIncludes(String includes) {
            this.includes = includes;
        }
        public void setExcludes(String excludes) {
            this.excludes = excludes;
        }
        
    }
    
    private File basedir = new File(".");
    private String runtime;
    private String out;
    private Vector<SourceFolderEntry> srcs = new Vector<SourceFolderEntry>();
    private Vector<FileSet> libs;

    @SuppressWarnings("unchecked")
    @Override
    public void doExecute() throws BuildException {
        Collection<IvyCacheEntry> entries;
        
        prepareAndCheck();

        try {
            entries = aggregate(getArtifactReports());
        } catch (Exception e) {
            throw new BuildException(e);
        }
        createEclipseClasspath(entries);
    }
    
    private Collection<IvyCacheEntry> aggregate(List<ArtifactDownloadReport> reports) {
        HashMap<String, IvyCacheEntry> entries = new HashMap<String, IvyCacheEntry>();
        
        for (ArtifactDownloadReport report : reports) {
            Artifact artifact = report.getArtifact();
            
            String key = getArtifactKey(artifact);
            if(! entries.containsKey(key)) {
                entries.put(key, new IvyCacheEntry(report));
            }
            IvyCacheEntry entry = entries.get(key);
            entry.merge(report);
        }
        
        return entries.values();
    }

    private void createEclipseClasspath(Collection<IvyCacheEntry> entries) throws BuildException {
        try {
            Document doc = DocumentBuilderFactory.newInstance()
                    .newDocumentBuilder().newDocument();
            Element root = doc.createElement("classpath");
            doc.appendChild(root);

            // Sources
            if(srcs!=null) {
                for (SourceFolderEntry sfe : srcs) {
                    Element item = doc.createElement("classpathentry");
                    item.setAttribute("kind", "src");
                    item.setAttribute("path", sfe.dir);
                    if (sfe.includes!=null) {
                        item.setAttribute("including", sfe.includes);
                    }
                    if (sfe.excludes!=null) {
                        item.setAttribute("excluding", sfe.excludes);
                    }
                    root.appendChild(item);
                }
            }
            
            // JRE
            Element rt = doc.createElement("classpathentry");
            if (runtime == null) {
                runtime = "JavaSE-1.6";
            }
            rt.setAttribute("kind", "con");
            rt.setAttribute("path", ECLIPSE_STANDARD_VM_PREFIX + runtime);
            root.appendChild(rt);
            
            // Ivy Dependencies
            for (IvyCacheEntry entry : entries) {
                if(entry.binary == null) 
                    continue;
                
                Element item = doc.createElement("classpathentry");
                item.setAttribute("kind", "lib");
                item.setAttribute("path", entry.binary.getAbsolutePath());
                if(entry.sources!=null) {
                    item.setAttribute("sourcepath", entry.sources.getAbsolutePath());
                }
                root.appendChild(item);
            }
            
            // lib
            if(libs!=null) {
                for(FileSet lib : libs) {
                    @SuppressWarnings("unchecked")
                    Iterator<FileResource> itr = lib.iterator();
                    
                    while(itr.hasNext()) {
                        FileResource res = itr.next();
                        
                        Element item = doc.createElement("classpathentry");
                        item.setAttribute("kind", "lib");
                        item.setAttribute("path", relatival(res.getFile(), basedir));
                        root.appendChild(item);
                    }
                }
            }
            
            // output
            if (out == null) {
                out = "bin";
            }
            Element output = doc.createElement("classpathentry");
            output.setAttribute("kind", "output");
            output.setAttribute("path", relatival(new File(out), basedir));
            root.appendChild(output);
            
            // write .classpath
            TransformerFactory tf = TransformerFactory.newInstance();
            Transformer transformer = tf.newTransformer();
            transformer.setOutputProperty(OutputKeys.INDENT, "yes");
            transformer.setOutputProperty("{http://xml.apache.org/xslt}indent-amount", "2");
            transformer.transform(new DOMSource(doc), new StreamResult(new File(basedir, ".classpath")));
        } catch (Exception e) {
            throw new BuildException();
        }
        
    }
    
    public void setBasedir(String basedir) {
        this.basedir = new File(basedir);
    }
    
    public void setRuntime(String runtime) {
        if (runtime.startsWith("1.")) {
            int minor = Integer.parseInt(runtime.substring(runtime.indexOf(".")+1));
            
            switch(minor) {
            case 8:
            case 7:
            case 6:
                this.runtime = "JavaSE-" + runtime;
                break;
            case 5:
            case 4:
            case 3:
            case 2:
                this.runtime = "J2SE-" + runtime;
                break;
            case 1:
                this.runtime = "JRE-1.1";
                break;
            default:
                this.runtime = "JavaSE-1.5";
            }
        } else {
            this.runtime = runtime;
        }
    }
    
    public void setOut(String out) {
        this.out = out;
    }
    
    public void addSrcfolder(SourceFolderEntry sfe) {
        srcs.add(sfe);
    }
    
    public void addLib(FileSet fs) {
        if(libs==null) {
            libs = new Vector<FileSet>();
        }
        libs.add(fs);
    }

}
