"""
Permite executar a API com: python -m qualia.api
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("qualia.api:app", host="127.0.0.1", port=8000)