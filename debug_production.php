<?php
// Script de Diagnóstico de Produção (Debug 500)
// Coloque na raiz do site (public_html) e acesse via navegador.

echo "<h1>Diagnóstico de Produção PureteGO</h1>";
echo "<pre>";

// 1. Verificar diretório atual e listar arquivos
echo "<h2>1. Arquivos no Diretório Atual</h2>";
echo "Diretório: " . getcwd() . "\n";
$files = scandir('.');
print_r($files);

// 2. Tentar ler log de erros do Python (comum em cPanel/Passenger)
echo "\n<h2>2. Logs de Erro (Últimas 50 linhas)</h2>";
$log_files = ['stderr.log', 'error_log', 'passenger_wsgi.log', 'logs/stderr.log'];
$found_log = false;

foreach ($log_files as $file) {
    if (file_exists($file)) {
        echo "Lendo arquivo: $file\n";
        echo "--------------------------------------------------\n";
        // Ler últimas 50 linhas
        $lines = file($file);
        $last_lines = array_slice($lines, -50);
        foreach ($last_lines as $line) {
            echo htmlspecialchars($line);
        }
        echo "\n--------------------------------------------------\n";
        $found_log = true;
    }
}

if (!$found_log) {
    echo "Nenhum arquivo de log padrão encontrado.\n";
}

// 3. Teste de Importação Python (Simular execução)
echo "\n<h2>3. Teste de Importação Python</h2>";
// Tenta rodar um comando python simples para ver se o app carrega
// Ajuste 'python3' ou o caminho do venv se souber (ex: ./venv/bin/python)
$python_cmd = "python3 -c \"import sys; print(sys.path); from app import create_app; app = create_app(); print('SUCCESS: App created')\" 2>&1";
echo "Executando: $python_cmd\n";
$output = shell_exec($python_cmd);
echo "Saída:\n" . htmlspecialchars($output);

echo "</pre>";
?>
