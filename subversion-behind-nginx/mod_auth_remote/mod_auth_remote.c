/* Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "apr_strings.h"
#include "apr_lib.h"            /* for apr_isspace */
#include "apr_base64.h"         /* for apr_base64_decode et al */
#define APR_WANT_STRFUNC        /* for strcasecmp */
#include "apr_want.h"

#include "ap_config.h"
#include "httpd.h"
#include "http_config.h"
#include "http_core.h"
#include "http_log.h"
#include "http_protocol.h"
#include "http_request.h"
#include "ap_provider.h"
#include "ap_expr.h"

#include "mod_auth.h"

module AP_MODULE_DECLARE_DATA auth_remote_module; 

typedef struct {
    char *remote_header;
    int remote_header_set;
} auth_remote_config_rec;

static void *create_auth_remote_dir_config(apr_pool_t *p, char *d) {
    auth_remote_config_rec *conf = apr_pcalloc(p, sizeof(auth_remote_config_rec));
    return conf;
}

static void *merge_auth_remote_dir_config(apr_pool_t *p, void *basev, void *overridesv) {
    auth_remote_config_rec *newconf = apr_pcalloc(p, sizeof(auth_remote_config_rec));
    auth_remote_config_rec *base = (auth_remote_config_rec *) basev;
    auth_remote_config_rec *overrides = (auth_remote_config_rec *) overridesv;

    newconf->remote_header =
        overrides->remote_header_set ? overrides->remote_header : base->remote_header;
    newconf->remote_header_set = overrides->remote_header_set || base->remote_header_set;
}

static const char *set_auth_remote_header(cmd_parms *cmd, void *config, const char *header) {
    auth_remote_config_rec *conf = (auth_remote_config_rec *) config;
    conf->remote_header = apr_pstrdup(cmd->pool, header);
    conf->remote_header_set = 1;
    return NULL;
}

static const command_rec auth_remote_cmds[] = {
    AP_INIT_TAKE1("AuthRemoteHeader", set_auth_remote_header, NULL, OR_AUTHCFG,
                  "Specific HTTP Header contains username"),
    {NULL}
};

static int authenticate_remote(request_rec *r) {
    auth_remote_config_rec *conf = ap_get_module_config(r->per_dir_config,
                                                        &auth_remote_module);
    const char *current_auth;

    current_auth = ap_auth_type(r);
    if (!current_auth || strcasecmp(current_auth, "Remote")) {
        return DECLINED;
    }

    if (! conf->remote_header_set) {
        ap_log_rerror(APLOG_MARK, APLOG_ERR, 0, r, APLOGNO(02101)
                      "need AuthRemoteHeader: %s", r->uri);
        return HTTP_INTERNAL_SERVER_ERROR;
    }

    r->ap_auth_type = (char *) current_auth;
    const char *remote_user = apr_table_get(r->headers_in, conf->remote_header);
    r->user = apr_pstrdup(r->pool, remote_user);
    return remote_user ? OK : HTTP_UNAUTHORIZED;
}

static void register_hooks(apr_pool_t *p) {
    ap_hook_check_authn(authenticate_remote, NULL, NULL, APR_HOOK_MIDDLE,
                        AP_AUTH_INTERNAL_PER_CONF);
}

AP_DECLARE_MODULE(auth_remote) =
{
    STANDARD20_MODULE_STUFF,
    create_auth_remote_dir_config,  /* dir config creater */
    merge_auth_remote_dir_config,   /* dir merger --- default is to override */
    NULL,                           /* server config */
    NULL,                           /* merge server config */
    auth_remote_cmds,               /* command apr_table_t */
    register_hooks                  /* register hooks */
};
