import pandas as pd

dados = {"nome" : ["Allan", "Juliana"], "idade" : [27,25]}

df = pd.DataFrame(dados)

df = pd.DataFrame(dados)

df.to_csv("estoque.csv", index=False)
print("Info salva com sucess")