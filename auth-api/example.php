<?php
/**
 * Exemplo: como o PHP chama a FastAPI após autenticar o usuário
 * Cole esta lógica no seu controller de login existente
 */

// ─── após validar login/senha normalmente no PHP ─────────────────────────────

$usuario_codigo  = 42;          // vem do banco após validar login/senha
$conta_codigo    = 7;           // cntContas_codigo do usuário
$ip_usuario      = $_SERVER['REMOTE_ADDR'];

$auth_api_url    = 'http://auth-api:8001';   // interno Docker
// se PHP roda fora do Docker: 'http://localhost:8001'

// ─── chama FastAPI para gerar o token ────────────────────────────────────────

$payload = json_encode([
    'usuario_codigo' => $usuario_codigo,
    'conta_codigo'   => $conta_codigo,
    'ip'             => $ip_usuario,
]);

$ch = curl_init("{$auth_api_url}/auth/token");
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST           => true,
    CURLOPT_POSTFIELDS     => $payload,
    CURLOPT_HTTPHEADER     => [
        'Content-Type: application/json',
        'Content-Length: ' . strlen($payload),
    ],
    CURLOPT_TIMEOUT        => 5,
]);

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($http_code !== 200) {
    // erro na API — trate conforme seu sistema
    die('Erro ao gerar token de sessão');
}

$data  = json_decode($response, true);
$token = $data['token'];

// ─── seta o cookie httpOnly no browser ───────────────────────────────────────
// httpOnly  → JavaScript não consegue ler
// Secure    → só trafega em HTTPS
// SameSite  → proteção contra CSRF

setcookie(
    'session_token',           // mesmo nome que COOKIE_NAME no .env
    $token,
    [
        'expires'  => strtotime($data['expira_em']),
        'path'     => '/',
        'domain'   => '.suaempresa.com',   // ajuste para seu domínio
        'secure'   => true,
        'httponly' => true,
        'samesite' => 'Lax',
    ]
);

// ─── redireciona de volta para onde o usuário queria ir ──────────────────────
$from = $_GET['from'] ?? 'https://superset.suaempresa.com';
header("Location: {$from}");
exit;


// ─── LOGOUT: PHP chama a API para invalidar o token ──────────────────────────
function logout_superset(string $token, string $auth_api_url): void
{
    $cookie_header = 'session_token=' . $token;

    $ch = curl_init("{$auth_api_url}/auth/logout");
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST           => true,
        CURLOPT_HTTPHEADER     => [
            'Cookie: ' . $cookie_header,
        ],
        CURLOPT_TIMEOUT => 5,
    ]);
    curl_exec($ch);
    curl_close($ch);

    // limpa o cookie no browser
    setcookie('session_token', '', time() - 3600, '/', '.suaempresa.com', true, true);
}