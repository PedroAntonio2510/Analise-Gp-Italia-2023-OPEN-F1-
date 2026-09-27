import os

import pandas as pd
import matplotlib.pyplot as plt

from pymongo import MongoClient
from dotenv import load_dotenv


# ============================================================
# CONFIGURAÇÃO
# ============================================================

load_dotenv()

MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017"
)

DATABASE_NAME = "openf1"

SESSION_KEY = 9159

PILOTOS = {
    16: "Charles Leclerc",
    55: "Carlos Sainz"
}


# ============================================================
# CONEXÃO COM MONGODB
# ============================================================

def conectar_mongodb():

    print("Conectando ao MongoDB...")

    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5000
    )

    client.admin.command("ping")

    print("MongoDB conectado com sucesso.")

    return client


# ============================================================
# BUSCAR DADOS
# ============================================================

def buscar_voltas(db):

    print(
        f"Buscando voltas da sessão {SESSION_KEY}..."
    )

    collection = db["laps"]

    dados = list(
        collection.find(
            {
                "session_key": SESSION_KEY,
                "driver_number": {
                    "$in": list(PILOTOS.keys())
                }
            },
            {
                "_id": 0,
                "session_key": 1,
                "driver_number": 1,
                "lap_number": 1,
                "lap_duration": 1,
                "date_start": 1
            }
        ).sort(
            [
                ("driver_number", 1),
                ("lap_number", 1)
            ]
        )
    )

    if not dados:

        raise ValueError(
            "Nenhuma volta encontrada no MongoDB."
        )

    print(
        f"{len(dados)} registros encontrados."
    )

    return dados


# ============================================================
# PREPARAR DATAFRAME
# ============================================================

def preparar_dataframe(dados):

    df = pd.DataFrame(dados)

    df["piloto"] = df["driver_number"].map(
        PILOTOS
    )

    # Remove voltas sem tempo
    df = df.dropna(
        subset=["lap_duration"]
    )

    # Remove tempos impossíveis
    df = df[
        df["lap_duration"] > 0
    ]

    return df


# ============================================================
# RESUMO DOS PILOTOS
# ============================================================

def mostrar_resumo(df):

    print("\n")
    print("=" * 60)
    print("RESUMO DO GP DA ITÁLIA 2023")
    print("=" * 60)

    for numero, nome in PILOTOS.items():

        piloto = df[
            df["driver_number"] == numero
        ]

        if piloto.empty:
            continue

        melhor_volta = piloto[
            "lap_duration"
        ].min()

        media = piloto[
            "lap_duration"
        ].mean()

        voltas = len(piloto)

        print(f"\nPiloto: {nome}")
        print(f"Voltas analisadas: {voltas}")
        print(
            f"Melhor volta: "
            f"{melhor_volta:.3f} s"
        )
        print(
            f"Média dos tempos: "
            f"{media:.3f} s"
        )


# ============================================================
# IDENTIFICAR VOLTAS MUITO LENTAS
# ============================================================

def identificar_pit_stops(df):

    print("\n")
    print("=" * 60)
    print("POSSÍVEIS PIT STOPS / VOLTAS FORA DO RITMO")
    print("=" * 60)

    for numero, nome in PILOTOS.items():

        piloto = df[
            df["driver_number"] == numero
        ].copy()

        if piloto.empty:
            continue

        # Tempo médio
        media = piloto[
            "lap_duration"
        ].mean()

        # Consideramos anormal uma volta
        # 20% mais lenta que a média
        limite = media * 1.20

        voltas_lentas = piloto[
            piloto["lap_duration"] > limite
        ]

        print(f"\n{nome}")

        if voltas_lentas.empty:

            print(
                "Nenhuma volta significativamente "
                "acima da média."
            )

        else:

            for _, volta in voltas_lentas.iterrows():

                print(
                    f"Volta {int(volta['lap_number'])}: "
                    f"{volta['lap_duration']:.3f}s"
                )


# ============================================================
# COMPARAÇÃO POR VOLTA
# ============================================================

def comparar_pilotos(df):

    print("\n")
    print("=" * 60)
    print("COMPARAÇÃO DOS PILOTOS")
    print("=" * 60)

    tabela = df[
        [
            "lap_number",
            "driver_number",
            "piloto",
            "lap_duration"
        ]
    ].copy()

    tabela = tabela.sort_values(
        [
            "lap_number",
            "driver_number"
        ]
    )

    print(
        tabela.to_string(
            index=False
        )
    )


# ============================================================
# GRÁFICO
# ============================================================

def gerar_grafico(df):

    print("\nGerando gráfico...")

    plt.figure(
        figsize=(14, 7)
    )

    for numero, nome in PILOTOS.items():

        piloto = df[
            df["driver_number"] == numero
        ].sort_values(
            "lap_number"
        )

        plt.plot(
            piloto["lap_number"],
            piloto["lap_duration"],
            marker="o",
            markersize=3,
            label=nome
        )

    plt.title(
        "GP da Itália 2023 - Comparação de Ritmo"
    )

    plt.xlabel(
        "Volta"
    )

    plt.ylabel(
        "Tempo de volta (segundos)"
    )

    plt.legend()

    plt.grid(
        True,
        alpha=0.3
    )

    plt.tight_layout()

    plt.savefig(
        "gp_italia_2023_leclerc_sainz.png",
        dpi=150
    )

    plt.show()

    print(
        "Gráfico salvo como "
        "'gp_italia_2023_leclerc_sainz.png'."
    )


# ============================================================
# EXPORTAR CSV
# ============================================================

def exportar_csv(df):

    arquivo = (
        "gp_italia_2023_leclerc_sainz.csv"
    )

    df.to_csv(
        arquivo,
        index=False
    )

    print(
        f"Dados exportados para {arquivo}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    client = None

    try:

        # --------------------------------------------
        # 1. CONEXÃO
        # --------------------------------------------

        client = conectar_mongodb()

        db = client[DATABASE_NAME]

        # --------------------------------------------
        # 2. EXTRAÇÃO
        # --------------------------------------------

        dados = buscar_voltas(db)

        # --------------------------------------------
        # 3. TRANSFORMAÇÃO
        # --------------------------------------------

        df = preparar_dataframe(
            dados
        )

        # --------------------------------------------
        # 4. ANÁLISE
        # --------------------------------------------

        mostrar_resumo(df)

        identificar_pit_stops(df)

        comparar_pilotos(df)

        # --------------------------------------------
        # 5. VISUALIZAÇÃO
        # --------------------------------------------

        gerar_grafico(df)

        # --------------------------------------------
        # 6. EXPORTAÇÃO
        # --------------------------------------------

        exportar_csv(df)

        print("\n")
        print("=" * 60)
        print(
            "ANÁLISE FINALIZADA COM SUCESSO!"
        )
        print("=" * 60)

    except Exception as error:

        print(
            f"\nErro durante a análise: {error}"
        )

    finally:

        if client:

            client.close()

            print(
                "Conexão com MongoDB encerrada."
            )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    main()