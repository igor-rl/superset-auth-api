# Auth - API
Api precifica para realizar a validação de autenticação do usuario no superset


### Abrir um tunnel com ssh para o banco pfcAccount
```cmd
sshpass -p '********' ssh -o StrictHostKeyChecking=no -L 0.0.0.0:3306:172.16.1.19:3306  igorlage@132.226.249.43
```

### teste de connexão com o tunnel
```cmd
docker run --rm alpine nc -zv host.docker.internal 3306
```

### health check
```cmd
curl http://localhost:8001/health
```

### /verify sem cookie — deve retornar 401
```cmd
curl -v http://localhost:8001/auth/verify
```

### Buscar um token valido no banco de dados
```sql
SELECT 
    codigo, 
    nome, 
    login, 
    regravar_token, 
    data_expiracao, 
    ativo, 
    excluido
FROM pfcAccount.cntUsuarios
WHERE 
    regravar_token IS NOT NULL     -- Precisa ter um token gerado
    AND ativo = 1                  -- Usuário precisa estar ativo
    AND excluido = 0               -- Usuário não pode estar deletado
    AND data_expiracao >= CURDATE() -- O token não pode ter vencido
ORDER BY data_expiracao DESC       -- Mostra os que demoram mais a vencer primeiro
LIMIT 10;
```

### /verify com cookie — deve retornar 200 
```cmd
curl -v http://localhost:8001/auth/verify --cookie "session_token=6fb8884dcb3c99d58af2c44bd4dcc64b"
```

### verificar os logs
```cmd
docker compose logs auth-api --tail=30
```


# Teste Nginx


### O Teste do "Porteiro" (Bloqueio)
Esperado retorno 302
```cmd
curl -I http://localhost/
```

### O Teste de "Identidade" (Acesso com Cookie)
Esperado 204
```cmd
curl -I http://localhost/ --cookie "session_token=6fb8884dcb3c99d58af2c44bd4dcc64b"
```