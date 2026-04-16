# Auth API — SSO entre PHP e Apache Superset

API FastAPI responsável por validar a autenticação do usuário no Superset via cookie de sessão gerado pelo sistema PHP (precifica).

---

## Arquitetura do Fluxo SSO

```
Browser → Nginx → auth_request → auth-api → MySQL (pfcAccount)
                ↓
           Superset (com X-User-Login header)
                ↓
       CustomSsoSecurityManager (request_loader)
                ↓
           Usuário autenticado no Superset
```

### Fluxo detalhado

1. Browser acessa `http://localhost/`
2. Nginx intercepta e faz `auth_request` para `/auth/verify` (interno)
3. auth-api lê o cookie `session_token`, valida no banco MySQL (`pfcAccount.cntUsuarios`)
4. Se válido → retorna 200 com headers `X-User-Id`, `X-User-Login`, `X-Empresa-Id`
5. Nginx injeta esses headers na requisição para o Superset
6. `CustomSsoSecurityManager.request_loader()` lê `X-User-Login` e autentica o usuário
7. Se inválido ou sem cookie → Nginx redireciona para `PHP_LOGIN_URL`

---

## Estrutura de Arquivos

```
auth-api/
├── Dockerfile
├── main.py                     # Entry point FastAPI + lifespan
├── requirements.txt
└── app/
    ├── config.py               # Settings via pydantic-settings
    ├── database/
    │   └── connection.py       # SQLAlchemy async engine
    ├── models/
    │   └── usuario.py          # ORM CntUsuarios + Pydantic UsuarioValidado
    ├── routes/
    │   ├── verify.py           # GET /auth/verify (usado pelo Nginx)
    │   ├── logout.py           # GET /auth/logout (redireciona para PHP)
    │   ├── token.py            # POST /auth/token (PHP chama após login)
    │   └── guest_token.py      # GET /auth/guest-token (embed de dashboards)
    └── services/
        ├── auth_service.py     # Validação de token no banco
        └── superset_service.py # Guest token via API do Superset

docker/
├── nginx/
│   └── templates/
│       └── superset.conf.template  # Configuração Nginx com auth_request
└── pythonpath_dev/
    ├── superset_config.py          # Configuração do Superset (AUTH, Redis, Celery)
    └── custom_sso_security_manager.py  # request_loader SSO
```

---

## Pré-requisitos

### Tunnel SSH para o banco pfcAccount

O banco MySQL fica em uma rede interna acessível via tunnel SSH:

```bash
sshpass -p 'SENHA' ssh -o StrictHostKeyChecking=no \
  -L 0.0.0.0:3306:172.16.1.19:3306 \
  igorlage@132.226.249.43
```

Teste se o tunnel está ativo (de dentro do Docker):

```bash
docker run --rm alpine nc -zv host.docker.internal 3306
```

---

## Variáveis de Ambiente

Definidas em `docker/.env` (não versionado). Referência:

```env
# Banco MySQL (pfcAccount via tunnel SSH)
DB_HOST=host.docker.internal
DB_PORT=3306
DB_NAME=pfcAccount
DB_USER=...
DB_PASSWORD=...

# API
API_ENV=production
API_SECRET_KEY=...

# Cookie
COOKIE_NAME=session_token
COOKIE_SECRET=...

# Superset
SUPERSET_URL=http://superset:8088
SUPERSET_ADMIN_USER=admin
SUPERSET_ADMIN_PASSWORD=...

# PHP
PHP_LOGIN_URL=https://precifica.app.br/user/login_web
PHP_LOGOUT_URL=https://precifica.app.br/user/logout
PHP_BASE_URL=https://precifica.app.br

# Nginx
PHP_LOGIN_URL=https://precifica.app.br/user/login_web
```

---

## Como rodar

```bash
# Subir tudo
docker compose up -d

# Acompanhar logs da auth-api
docker compose logs auth-api -f

# Acompanhar logs do Superset
docker compose logs superset -f --no-log-prefix | grep -v DEBUG
```

---

## Testes

### 1. Tunnel SSH ativo?

```bash
docker run --rm alpine nc -zv host.docker.internal 3306
# Esperado: open
```

### 2. auth-api health check

```bash
curl http://localhost:8001/health
# Esperado: {"status":"ok"}
```

### 3. Buscar token válido no banco

```sql
SELECT codigo, nome, login, regravar_token, data_expiracao, ativo, excluido
FROM pfcAccount.cntUsuarios
WHERE regravar_token IS NOT NULL
  AND ativo = 1
  AND excluido = 0
  AND data_expiracao >= CURDATE()
ORDER BY data_expiracao DESC
LIMIT 10;
```

### 4. Verificar autenticação — direto na auth-api (bypass Nginx)

```bash
# Sem cookie → deve retornar 401
curl -v http://localhost:8001/auth/verify
# Esperado: HTTP/1.1 401 — "sem token"

# Com cookie válido → deve retornar 200 com headers X-User-*
curl -v http://localhost:8001/auth/verify \
  --cookie "session_token=SEU_TOKEN_AQUI"
# Esperado: HTTP/1.1 200
#   x-user-id: 5161
#   x-empresa-id: 1084
#   x-user-login: usuario@empresa.com
```

### 5. Verificar autenticação — via Nginx

```bash
# Sem cookie → deve redirecionar para PHP login
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" http://localhost/
# Esperado: 302 https://precifica.app.br/user/login_web?from=http://localhost/

# Com cookie válido → deve entrar no Superset
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" \
  http://localhost/ \
  --cookie "session_token=SEU_TOKEN_AQUI"
# Esperado: 302 http://localhost/superset/welcome/
```

### 6. Testar login completo no browser

Abra `http://localhost/` sem cookie de sessão. Deve redirecionar para o login PHP.
Após login no PHP, o cookie `session_token` é setado e o Superset carrega autenticado.

### 7. Testar logout

```bash
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" \
  http://localhost/auth/logout \
  --cookie "session_token=SEU_TOKEN_AQUI"
# Esperado: 302 https://precifica.app.br/user/logout (PHP invalida o token)
```

### 8. Testar guest token (embed de dashboard)

```bash
curl "http://localhost:8001/auth/guest-token?dashboard_id=UUID_DO_DASHBOARD" \
  --cookie "session_token=SEU_TOKEN_AQUI"
# Esperado: {"guest_token":"..."}
```

### 9. Verificar logs pós-acesso

```bash
# Ver últimas requisições na auth-api
docker compose logs auth-api --tail=20

# Ver logs relevantes do Superset (sem ruído de DEBUG)
docker compose logs superset --tail=100 2>&1 | grep -v DEBUG | grep -v inotify | tail -30

# Ver logs do Nginx
docker compose logs nginx --tail=30
```

---

## Como o PHP integra

Após validar login/senha, o PHP chama `POST /auth/token` para gerar o token e setar o cookie:

```php
// Ver auth-api/example.php para implementação completa
$payload = json_encode([
    'usuario_codigo' => $usuario_codigo,
    'conta_codigo'   => $conta_codigo,
    'ip'             => $_SERVER['REMOTE_ADDR'],
]);

// Chama a auth-api
$ch = curl_init("http://auth-api:8001/auth/token");
// ...

// Seta o cookie httpOnly no browser
setcookie('session_token', $token, [
    'expires'  => strtotime($data['expira_em']),
    'path'     => '/',
    'secure'   => true,
    'httponly' => true,
    'samesite' => 'Lax',
]);
```

---

## CustomSsoSecurityManager

Localizado em `docker/pythonpath_dev/custom_sso_security_manager.py`.

Estende `SupersetSecurityManager` e sobrescreve `request_loader()` para autenticar via header HTTP `X-User-Login` (injetado pelo Nginx após validação do cookie). Cria o usuário automaticamente no primeiro acesso com a role definida em `AUTH_USER_REGISTRATION_ROLE`.

Registrado no `superset_config.py` via:

```python
from custom_sso_security_manager import CustomSsoSecurityManager
CUSTOM_SECURITY_MANAGER = CustomSsoSecurityManager
```

---

## Troubleshooting

| Sintoma | Causa provável | Solução |
|---|---|---|
| `curl /auth/verify` retorna 401 sem cookie | ✅ Comportamento correto | — |
| `curl /auth/verify` retorna 401 com cookie válido | Tunnel SSH caído ou token expirado | Reabrir tunnel, verificar data_expiracao |
| Superset mostra formulário de login | `CUSTOM_SECURITY_MANAGER` não registrado | Verificar tail do superset_config.py |
| 500 no Superset após autenticar | Erro no request_loader | `docker compose logs superset 2>&1 \| grep -v DEBUG \| grep -i error` |
| WebSocket 502 | superset-websocket não está rodando | `docker compose ps` e `docker compose logs superset-websocket` |
| Redirect para `/login/` mesmo com cookie | Header X-User-Login não chegando | Verificar bloco `auth_request_set` no nginx template |