import psycopg2
import pandas as pd

# function for filling a dataframe with a Redshift database query
def database_query(creds,thequery,colnames):
    conn = psycopg2.connect(database=creds["database"], 
                        user = creds["user"], password = creds["password"], 
                        host = creds["host"], port = creds["port"])
    cur = conn.cursor()
    cur.execute(thequery)
    df_toreturn = pd.DataFrame(cur.fetchall(), columns=colnames)
    conn.close()
    return df_toreturn

def database_query_withdtypes(creds,thequery,colnames=None):
    conn = psycopg2.connect(database=creds["database"], 
                        user = creds["user"], password = creds["password"], 
                        host = creds["host"], port = creds["port"])
    cur = conn.cursor()
    
    try:
        cur.execute(thequery)
    except Exception as e:
        raise e
    else:
        if colnames is None:
            colnames = [desc[0] for desc in cur.description]
        dtypecodes = [desc[1] for desc in cur.description]
        df_toreturn = pd.DataFrame(cur.fetchall(), columns=colnames)
        conn.close()
        return df_toreturn,dtypecodes

# prepares dataframe for export to csv
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')
    
    
def build_cursor(creds):
    conn = psycopg2.connect(database=creds["database"], 
                        user = creds["user"], password = creds["password"], 
                        host = creds["host"], port = creds["port"])
    cur = conn.cursor()
    return conn, cur
