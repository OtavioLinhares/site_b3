#!/bin/bash

echo "----------------------------------------------------------------"
echo "Iniciando compartilhamento seguro via Túnel SSH..."
echo "Certifique-se de que o site está rodando (npm run dev) em outra janela."
echo "----------------------------------------------------------------"

# Check if port 5173 is open (simple check)
if ! lsof -i :5173 > /dev/null; then
    echo "AVISO: Parece que o servidor local (Porta 5173) não está rodando."
    echo "Por favor, rode 'npm run dev' na pasta 'web' antes de usar este script."
    echo "Pressione ENTER para tentar mesmo assim ou Ctrl+C para cancelar."
    read -r
fi

echo "Gerando link público..."
echo "Copie o link https://... que aparecerá abaixo e envie para seu amigo."
echo "Pressione Ctrl+C para encerrar o compartilhamento."
echo "----------------------------------------------------------------"

# Create SSH tunnel forwarding remote port 80 to local 5173
# -R 80:localhost:5173 -> Remote port 80 forwards to Local 5173
# nokey@localhost.run -> The service user/host (no auth key needed)
ssh -R 80:localhost:5173 nokey@localhost.run
