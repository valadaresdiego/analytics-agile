#%%
import psycopg2
from faker import Faker
import random
from datetime import datetime, timedelta
import uuid

#%%
# Configuração
fake = Faker('pt_BR')
conn = psycopg2.connect(
    dbname="analytics_agile",
    user="postgres",
    password="Naiaradagola2406",
    host="localhost"
)
cursor = conn.cursor()

#%%
# Funções auxiliares
def random_date(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))

# 1. Criar membros da equipe
funcoes = ['Engenheiro de Dados', 'Cientista de Dados', 'Analista de BI', 'Product Owner', 'Scrum Master', 'Engenheiro ML']
niveis = ['Júnior', 'Pleno', 'Sênior', 'Especialista']

for _ in range(15):
    cursor.execute(
        "INSERT INTO membros_equipe (nome, email, funcao, nivel, data_contratacao) VALUES (%s, %s, %s, %s, %s)",
        (fake.name(), fake.email(), random.choice(funcoes), random.choice(niveis), fake.date_between(start_date='-5y', end_date='today'))
    )

#%%
# 2. Criar projetos
departamentos = ['Data Engineering', 'Analytics', 'BI', 'Data Science', 'AI']
status_projeto = ['Ativo', 'Concluído', 'Pausado', 'Cancelado']
projetos_ids = []

for i in range(1, 6):
    projeto_id = uuid.uuid4()
    projetos_ids.append(projeto_id)
    data_inicio = fake.date_between(start_date='-1y', end_date='today')
    data_termino = data_inicio + timedelta(days=random.randint(60, 180)) if random.random() > 0.3 else None
    
    cursor.execute(
        """INSERT INTO projetos 
        (projeto_id, nome, descricao, data_inicio, data_termino, orcamento, departamento, status) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (projeto_id,
         f"Projeto {' '.join(fake.words(3)).title()}",
         fake.text(max_nb_chars=200),
         data_inicio,
         data_termino,
         random.randint(50000, 500000),
         random.choice(departamentos),
         random.choices(status_projeto, weights=[0.5, 0.3, 0.1, 0.1])[0])
    )
#%%
# 3. Criar sprints
for projeto_id in projetos_ids:
    num_sprints = random.randint(3, 8)
    sprint_start = fake.date_between(start_date='-6m', end_date='today')
    
    for sprint_num in range(1, num_sprints + 1):
        sprint_end = sprint_start + timedelta(days=14)
        cursor.execute(
            """INSERT INTO sprints 
            (projeto_id, numero, data_inicio, data_termino, meta, velocidade_planejada, velocidade_real) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (projeto_id,
             sprint_num,
             sprint_start,
             sprint_end,
             fake.sentence(),
             random.randint(20, 50),
             random.randint(15, 55))
        )
        sprint_start = sprint_end + timedelta(days=1)
#%%
# 4. Criar tarefas
tipos_tarefa = ['Feature', 'Bug', 'Melhoria', 'Documentação', 'Pesquisa', 'Manutenção']
status_tarefa = ['Backlog', 'To Do', 'In Progress', 'Code Review', 'Testing', 'Done', 'Blocked']
complexidades = ['Baixa', 'Média', 'Alta']

#%%
# Obter IDs de membros
cursor.execute("SELECT membro_id FROM membros_equipe")
membros_ids = [row[0] for row in cursor.fetchall()]

for projeto_id in projetos_ids:
    num_tarefas = random.randint(20, 50)
    
    for _ in range(num_tarefas):
        tarefa_id = uuid.uuid4()
        data_criacao = fake.date_time_between(start_date='-6m', end_date='now')
        status = random.choices(status_tarefa, weights=[0.1, 0.15, 0.2, 0.15, 0.15, 0.2, 0.05])[0]
        
        # Definir datas baseadas no status
        data_inicio = data_conclusao = None
        if status in ['In Progress', 'Code Review', 'Testing', 'Done', 'Blocked']:
            data_inicio = data_criacao + timedelta(days=random.randint(0, 7))
        
        if status == 'Done':
            data_conclusao = data_inicio + timedelta(days=random.randint(1, 14))
        
        cursor.execute(
            """INSERT INTO tarefas 
            (tarefa_id, projeto_id, titulo, descricao, tipo, tamanho, prioridade, 
             data_criacao, data_inicio, data_conclusao, status, membro_responsavel, 
             estimativa_horas, complexidade) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (tarefa_id,
             projeto_id,
             f"{random.choice(['Implementar', 'Corrigir', 'Melhorar', 'Documentar', 'Analisar'])} {fake.word()}",
             fake.text(max_nb_chars=100),
             random.choice(tipos_tarefa),
             random.choice([1, 2, 3, 5, 8]),
             random.randint(1, 5),
             data_criacao,
             data_inicio,
             data_conclusao,
             status,
             random.choice(membros_ids) if random.random() > 0.3 else None,
             random.choice([4, 8, 12, 16, 20, 24, 32, 40]),
             random.choices(complexidades, weights=[0.4, 0.4, 0.2])[0])
        )
        # Criar histórico de status
        if status in ['In Progress', 'Code Review', 'Testing', 'Done', 'Blocked']:
            # Adicionar status anteriores
            status_possiveis = ['Backlog', 'To Do', 'In Progress', 'Code Review', 'Testing']
            current_status_index = status_possiveis.index(status) if status in status_possiveis else 2
            
            for i in range(random.randint(1, current_status_index + 1)):
                status_historico = status_possiveis[i] if i < len(status_possiveis) else status
                data_entrada = data_criacao + timedelta(days=random.randint(0, 3), hours=random.randint(1, 12))
                data_saida = data_entrada + timedelta(days=random.randint(1, 5)) if i < current_status_index else None
                
                cursor.execute(
                    """INSERT INTO historico_status 
                    (tarefa_id, status, data_entrada, data_saida, comentario) 
                    VALUES (%s, %s, %s, %s, %s)""",
                    (tarefa_id,
                     status_historico,
                     data_entrada,
                     data_saida,
                     fake.sentence() if random.random() > 0.7 else None)
                )
                if status == 'Blocked' and i == current_status_index:
                    cursor.execute(
                        """INSERT INTO historico_status 
                        (tarefa_id, status, data_entrada, data_saida, comentario) 
                        VALUES (%s, %s, %s, %s, %s)""",
                        (tarefa_id,
                         'Blocked',
                         data_entrada + timedelta(days=1),
                         data_entrada + timedelta(days=3),
                         'Bloqueado por dependência externa'))

conn.commit()
cursor.close()
conn.close()

print("Pipeline de ingestão concluído com sucesso!")