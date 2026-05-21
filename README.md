# 🌤️ Weather DataViewer Dashboard

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Highcharts](https://img.shields.io/badge/Highcharts-0081B4?style=for-the-badge&logo=highcharts&logoColor=white)](https://www.highcharts.com/)

Um dashboard completo para monitoramento de dados meteorológicos em tempo real, com visualizações interativas, armazenamento em banco de dados e simulação automática de sensores.

## 📋 Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Pré-requisitos](#pré-requisitos)
- [Instalação e Execução](#instalação-e-execução)
  - [Docker (Recomendado)](#docker-recomendado)
  - [Execução Local](#execução-local)
- [Endpoints da API](#endpoints-da-api)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Sensores Monitorados](#sensores-monitorados)
- [Uso do Dashboard](#uso-do-dashboard)
- [Deploy no Railway](#deploy-no-railway)
- [Solução de Problemas](#solução-de-problemas)
- [Contribuição](#contribuição)
- [Licença](#licença)

## 📖 Sobre o Projeto

O **Weather DataViewer Dashboard** é uma aplicação full-stack para monitoramento de dados meteorológicos. O sistema simula dados de 8 sensores diferentes, armazena em banco de dados PostgreSQL e apresenta visualizações interativas utilizando Highcharts.

**Dados simulados incluem:**

- Temperatura com ciclo diário realístico
- Umidade correlacionada com temperatura
- Pressão atmosférica com variação lenta
- Velocidade do vento com rajadas
- Radiação UV com pico ao meio-dia
- Luminosidade acompanhando radiação solar
- Pluviometria com eventos de chuva simulados
- CO2 com picos de atividade humana

## ✨ Funcionalidades

- **📊 Dashboard Interativo**
  - Gráficos de gauge para valores atuais
  - Gráficos de linha para séries temporais
  - Tabela sincronizada com dados históricos
  - Atualização automática de dados

- **🗄️ Backend Robusto**
  - API RESTful com FastAPI
  - Banco de dados PostgreSQL/TimescaleDB
  - Simulador automático de sensores
  - Backfill de dados históricos (7 dias)

- **🐳 Containerizado**
  - Docker Compose para fácil deploy
  - Pronto para deploy no Railway
  - Configuração de ambiente simplificada

- **📱 Responsivo**
  - Interface adaptável a diferentes tamanhos de tela
  - Gráficos com zoom e range selector
  - Download de dados em CSV

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Versão  | Finalidade                   |
| ---------- | ------- | ---------------------------- |
| FastAPI    | 0.115.0 | API backend                  |
| Python     | 3.12    | Linguagem principal          |
| PostgreSQL | 15      | Banco de dados               |
| asyncpg    | 0.29.0  | Driver assíncrono PostgreSQL |
| Pydantic   | 2.8.2   | Validação de dados           |
| Uvicorn    | 0.30.6  | Servidor ASGI                |
| Docker     | Latest  | Containerização              |
| Highcharts | Latest  | Visualização de dados        |
| jQuery     | 3.6.0   | Manipulação DOM              |

## 📋 Pré-requisitos

- **Docker** e **Docker Compose** (recomendado)
- **Python 3.12+** (para execução local)
- **PostgreSQL 15+** (para execução local)
- **Git** (para clonar o repositório)
- Navegador moderno (Chrome, Firefox, Edge)

## 🚀 Instalação e Execução

### Docker (Recomendado)

1. **Clone o repositório:**

```bash
git clone https://github.com/LeoAChaves/DataViewer_Dashboard.git
cd DataViewer_Dashboard
```

2. **Inicie os containers:**

```bash
docker-compose up -d
```

3. **Aguarde o backfill de dados (cerca de 30 segundos):**

```bash
docker-compose logs -f api
```

Aguarde até ver: `[backfill] Done — 16,136 rows inserted.`

4. **Acesse o dashboard:**

```
http://localhost:8000/?session=demo
```

### Execução Local (Sem Docker)

1. **Instale as dependências:**

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

2. **Configure o PostgreSQL:**

```bash
# Certifique-se que o PostgreSQL está rodando
sudo service postgresql start  # Linux
# ou inicie o serviço no Windows
```

3. **Configure a variável de ambiente:**

```bash
# Linux/Mac
export DATABASE_URL="postgresql://postgres:password@localhost:5432/weatherdb"

# Windows PowerShell
$env:DATABASE_URL="postgresql://postgres:password@localhost:5432/weatherdb"
```

4. **Execute a aplicação:**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. **Acesse o dashboard:**

```
http://localhost:8000/?session=demo
```

## 🔌 Endpoints da API

| Método | Endpoint                     | Descrição                   |
| ------ | ---------------------------- | --------------------------- |
| GET    | `/`                          | Dashboard principal         |
| GET    | `/health`                    | Health check da API         |
| GET    | `/sessions`                  | Lista todas as sessões      |
| GET    | `/session/{session_id}`      | Lista tópicos de uma sessão |
| GET    | `/data/{session_id}/{topic}` | Obtém dados de um tópico    |
| POST   | `/sessions/{session_id}`     | Cria uma nova sessão        |
| POST   | `/ingest`                    | Insere dados manualmente    |
| GET    | `/docs`                      | Documentação Swagger UI     |
| GET    | `/redoc`                     | Documentação ReDoc          |

### Exemplos de Uso da API

```bash
# Listar sessões
curl http://localhost:8000/sessions

# Criar nova sessão
curl -X POST http://localhost:8000/sessions/minha_estacao

# Ver tópicos disponíveis
curl http://localhost:8000/session/demo

# Obter dados de temperatura
curl "http://localhost:8000/data/demo/Temperatura?limit=10"

# Inserir dado manualmente
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo","topic":"Temperatura","value":23.5}'
```

## 📁 Estrutura do Projeto

```
weather-dashboard/
├── app/
│   ├── __init__.py
│   ├── database.py          # Configuração do banco de dados
│   ├── main.py              # Aplicação FastAPI principal
│   ├── models.py            # Modelos Pydantic
│   └── simulator.py         # Simulador de sensores
├── src/
│   └── css/
│       ├── dataViewer.css
│       ├── gaugeConfig.css
│       └── syncedTableLine.css
├── js/
│   ├── dataViewer.js
│   ├── gaugeConfig.js
│   └── syncedTableLine.js
├── dataViewer.html          # Dashboard principal
├── requirements.txt         # Dependências Python
├── Dockerfile              # Configuração Docker
├── docker-compose.yml      # Orquestração Docker
└── README.md               # Documentação
```

## 🌡️ Sensores Monitorados

| Sensor              | Unidade | Faixa Típica | Descrição                           |
| ------------------- | ------- | ------------ | ----------------------------------- |
| Temperatura         | °C      | -5 a 45      | Ciclo diário com variação sazonal   |
| Umidade             | %       | 10 a 100     | Correlação inversa com temperatura  |
| Pressão             | hPa     | 980 a 1040   | Variação lenta (frentes climáticas) |
| Velocidade do Vento | m/s     | 0 a 30       | Distribuição gamma com rajadas      |
| Radiação UV         | W/m²    | 0 a 1200     | Pico ao meio-dia                    |
| Luminosidade        | Lux     | 0 a 120000   | Segue radiação UV                   |
| Pluviometria        | mm      | 0 a 50       | Eventos de chuva simulados          |
| CO2                 | ppm     | 350 a 2000   | Picos matutino/vespertino           |

## 📊 Uso do Dashboard

### Navegação Principal

1. **Gráficos de Gauge (Topo)**
   - Mostram valores atuais de cada sensor
   - Cores indicam faixa de medição
   - Atualização automática

2. **Gráficos de Linha (Centro)**
   - Histórico temporal dos dados
   - Zoom com seleção de intervalo (1h, 12h, 24h, All)
   - Tooltips interativos

3. **Tabela de Dados (Fundo)**
   - Últimos 73 registros (6 horas)
   - Destaque ao passar mouse
   - Download em CSV

### Recursos Interativos

- **Zoom**: Selecione uma área no gráfico para ampliar
- **Range Selector**: Botões pré-configurados para intervalos
- **Exportação**: Download dos dados da tabela em CSV
- **Responsividade**: Layout adapta-se ao tamanho da tela

## ☁️ Deploy no Railway

1. **Conecte seu repositório ao Railway:**
   - Acesse [railway.app](https://railway.app)
   - Clique em "New Project" → "Deploy from GitHub repo"

2. **Adicione um banco de dados PostgreSQL:**
   - Clique em "Create" → "Database" → "PostgreSQL"

3. **Configure as variáveis de ambiente:**
   - Railway fornecerá automaticamente `DATABASE_URL`

4. **Deploy automático:**
   - O Railway detectará o `Dockerfile` automaticamente
   - O projeto será construído e implantado

5. **Acesse sua aplicação:**
   - URL será fornecida pelo Railway (ex: `https://weather-dashboard.up.railway.app/?session=demo`)

## 🔧 Solução de Problemas

### Problema: "Session not found"

```bash
# Criar sessão manualmente
curl -X POST http://localhost:8000/sessions/demo
```

### Problema: Sem dados no dashboard

```bash
# Verificar se backfill foi executado
docker-compose logs api | grep backfill

# Forçar novo backfill
docker exec weather-api python -c "
import asyncio
from app.main import _backfill
from app.database import get_pool
asyncio.run(_backfill(get_pool()))
"
```

### Problema: Porta 8000 já em uso

```bash
# Usar porta diferente no docker-compose.yml
ports:
  - "8001:8000"
```

### Problema: Erro de conexão com PostgreSQL

```bash
# Verificar se o container do PostgreSQL está rodando
docker ps | grep postgres

# Verificar logs do PostgreSQL
docker-compose logs postgres
```

### Problema: Arquivos estáticos não carregam

```bash
# Verificar se os arquivos existem no container
docker exec weather-api ls -la /app/js/
docker exec weather-api ls -la /app/src/css/

# Recarregar sem cache no navegador
Ctrl + F5
```

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie sua branch de feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👥 Autores

- **Leonardo Chaves** - _Desenvolvimento Inicial_ - [SeuGitHub](https://github.com/LeoAChaves)

## 🙏 Agradecimentos

- [FastAPI](https://fastapi.tiangolo.com/) - Framework web incrível
- [Highcharts](https://www.highcharts.com/) - Bibliotecas de gráficos
- [Docker](https://www.docker.com/) - Containerização
- [Railway](https://railway.app/) - Plataforma de deploy

## 📊 Status do Projeto

![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Version](https://img.shields.io/badge/Version-2.0.0-blue)

---

⭐️ **Se este projeto foi útil para você, deixe uma estrela no GitHub!** ⭐️

📧 **Contato**: chaves.leonardoalmeida@gmail.com

🐛 **Reportar Bug**: [Issues](https://github.com/seuusuario/weather-dashboard/issues)
