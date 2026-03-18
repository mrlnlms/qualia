"""
Permite executar a API com: python -m qualia.api
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("qualia.api:app", host="0.0.0.0", port=8000)