"""Run ArgumentCraft locally.

In PyCharm: run this file (or use `uvicorn app.main:app --reload`).
"""

import uvicorn


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8013, reload=True)
