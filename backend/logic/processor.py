def process_files(repl1, repl2, dis1, dis2, output_path):
    import pandas as pd
    # Dummy gabung excel saja dulu
    df1 = pd.read_excel(repl1)
    df2 = pd.read_excel(repl2)
    df3 = pd.read_excel(dis1)
    df4 = pd.read_excel(dis2)

    combined = pd.concat([df1, df2, df3, df4])
    combined.to_excel(output_path, index=False)