import requests
import json
import urllib.parse

# Configurações
CPANEL_BASE_URL = "https://puretego.online:2083"
USERNAME = "puretego"
PASSWORD = "Kn16Nt]wB3O:3k"
REPO_PATH = "/home2/puretego/repositories/puretego-crm"
CLONE_URL = "https://github.com/PureteGO/puretego-crm.git"

def cpanel_api(module, function, params=None):
    if params is None:
        params = {}
    
    # UAPI endpoint
    url = f"{CPANEL_BASE_URL}/execute/{module}/{function}"
    
    print(f"Executing {module}::{function}...")
    try:
        response = requests.get(
            url,
            auth=(USERNAME, PASSWORD),
            params=params,
            verify=True # Verify SSL
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error calling API: {e}")
        return None

def main():
    print("--- INICIANDO CONFIGURAÇÃO AUTOMÁTICA DO CPANEL ---")

    # 1. Tentar criar (ou verificar) o repositório Git
    print("\n[1/3] Configurando Repositório Git...")
    # Docs: https://api.docs.cpanel.net/openapi/cpanel/operation/VersionControl-create/
    res_create = cpanel_api("VersionControl", "create", {
        "type": "git",
        "name": "puretego-crm",
        "repository_root": REPO_PATH,
        "source_repository": json.dumps({"url": CLONE_URL})
    })

    if res_create and res_create.get('status') == 1:
        print("✅ Repositório criado/verificado com sucesso!")
        print(f"   Caminho: {res_create['data']['repository_root']}")
    else:
        print("ℹ️  Status da criação do repositório (pode já existir):")
        if res_create:
             print(f"   Mensagem: {res_create.get('errors') or res_create.get('messages')}")
        else:
            print("   Falha na conexão.")

    # 2. Gerar Chave SSH se não existir
    KEY_NAME = "puretego_deploy"
    print(f"\n[2/3] Verificando Chaves SSH ({KEY_NAME})...")
    # Primeiro listamos para ver se existe
    res_list_keys = cpanel_api("SSH", "list_keys")
    key_exists = False
    if res_list_keys and res_list_keys.get('status') == 1:
        for key in res_list_keys['data']:
            if key['name'] == KEY_NAME:
                key_exists = True
                print(f"✅ Chave '{KEY_NAME}' já existe.")
                break
    
    if not key_exists:
        print(f"⚠️ Chave '{KEY_NAME}' não encontrada. Gerando nova chave...")
        res_gen = cpanel_api("SSH", "genkey", {
            "name": KEY_NAME,
            "password": "" # Sem senha para CI/CD
        })
        if res_gen and res_gen.get('status') == 1:
            print(f"✅ Nova chave SSH '{KEY_NAME}' gerada com sucesso.")
            # Autorizar a chave (importante!)
            cpanel_api("SSH", "authorize_key", {"name": f"{KEY_NAME}.pub"})
            print(f"✅ Chave '{KEY_NAME}' autorizada.")
        else:
            print("❌ Falha ao gerar chave SSH.")
            print(f"   Detalhes: {res_gen}")

    # 3. Obter a Private Key para exibir ao usuário
    print("\n[3/3] Recuperando Chave Privada para o GitHub...")
    # EDIT: We will attempt to use 'Fileman::get_file_content' to read .ssh/puretego_deploy
    
    res_read = cpanel_api("Fileman", "get_file_content", {
        "dir": ".ssh",
        "file": KEY_NAME
    })
    
    if res_read and res_read.get('status') == 1:
        private_key = res_read['data']['content']
        print("\nSUCCESS! AQUI ESTÁ A SUA CHAVE PRIVADA (Copie tudo abaixo para o GitHub Secret CPANEL_SSH_KEY):")
        print("================================================================================================")
        print(private_key)
        print("================================================================================================")
        
        # Salvar em arquivo para backup local seguro (opcional)
        backup_filename = f"{KEY_NAME}_local_backup.txt"
        with open(backup_filename, "w") as f:
            f.write(private_key)
        print(f"\n(Também salvei uma cópia em '{backup_filename}' caso precise)")
    else:
        print("❌ Não foi possível ler o arquivo da chave privada via API.")
        print("   Por favor, acesse o cPanel > SSH Access > Private Keys > View e copie manualmente.")

if __name__ == "__main__":
    main()
