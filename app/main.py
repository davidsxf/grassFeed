# import uvicorn


from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Header, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel, Field

# import models
from .models import Base

from .database import engine, SessionLocal
from sqlalchemy.orm import Session

# from logzero import logger


# torch
import torch


app = FastAPI()


class FeedBase(BaseModel):
    weight_range: str
    t_range: str
    coe_min: float
    coe_max: float
    weight_min: float
    weight_max: float
    t_min: float
    t_max: float
    fcr: float


Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


templates = Jinja2Templates(directory="templates")


def calculate_feeding_amount(weight: float, temperature: float, weight_range: str,
                             t_range: str, db: Session):
    """
    根据鱼的体重和水温计算饲料投喂量
    :param weight: 鱼的体重（单位：克）
    :param temperature: 水温（摄氏度）
    :return: 饲料投喂量（单位：克）

    区间化的目的是让数据压缩在【a，b】范围内，a和b是自己希望的区间值，如果a=0,b=1，
    那么其实就是一种特殊情况即归一化；
    其计算公式为a + (b - a) * (X - Min)/(Max - Min)。
    """

    # 假设您的数据模型中有一个 Fish 类和一个 FeedingSchedule 类
    # Fish 类包含鱼的信息，FeedingSchedule 类包含饲料投喂量的信息

    feed = db.query(models.Feeds).filter(models.Feeds.weight_range ==
                                         weight_range, models.Feeds.t_range == t_range).first()

    if not feed:
        raise HTTPException(
            status_code=404, detail="Feeding schedule not found")

        # 计算饲料投喂量
    t_coe = feed.coe_min + (feed.coe_max - feed.coe_min) * \
        (temperature - feed.t_min) / (feed.t_max - feed.t_min)
    w_coe = feed.coe_min + (feed.coe_max - feed.coe_min) * \
        (weight - feed.weight_min) / (feed.weight_max - feed.weight_min)
    coe = (t_coe + w_coe)/2
    return coe


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("index.html", context)


@app.get("/feed/", response_class=HTMLResponse)
async def index(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("predict.html", context)

@app.get("/index/", response_class=HTMLResponse)
async def movielist(request: Request, hx_request: Optional[str] = Header(None)):
    films = [
        {'name': 'Blade Runner', 'director': 'Ridley Scott'},
        {'name': 'Pulp Fiction', 'director': 'Quentin Tarantino'},
        {'name': 'Mulholland Drive', 'director': 'David Lynch'},
    ]
    context = {"request": request, 'films': films}
    if hx_request:
        return templates.TemplateResponse("partials/table.html", context)
    return templates.TemplateResponse("index.html", context)


@app.post("/calculate/", response_class=HTMLResponse)
async def calculate(request: Request, hx_request: Optional[str] = Header(None), weight: float = Form(...), temperature: float = Form(...),
                    weight_range: str = Form(...), t_range: str = Form(...), feeding_amount: float = Form(...), db: Session = Depends(get_db)):

    print(weight, temperature, weight_range, t_range, feeding_amount)
    coe = calculate_feeding_amount(
        weight, temperature, weight_range, t_range, db)
    amount = round(feeding_amount/coe / 500,1)
    context = {"request": request, "amount": amount, "coe": coe}
    if coe is None:
        raise HTTPException(
            status_code=404, detail="Feeding schedule not found")
    if hx_request:
        return templates.TemplateResponse("partials/result.html", context)
    return templates.TemplateResponse("index.html", context)


@app.post("/predict/", response_class=HTMLResponse)
async def predict(request: Request, hx_request: Optional[str] = Header(None),amount: float = Form(...),temper: float = Form(...),size: float = Form(...)):
    
    print(amount, temper, size)
    model = torch.load('data/feed_model.pth')
    X_one = torch.tensor([[amount, temper, size]], dtype=torch.float32)
    model.eval()
    y_pred = model(X_one).detach().numpy()[0][0]
    print(y_pred)
   
    context = {"request": request, "y_pred": y_pred}

    if hx_request:
        return templates.TemplateResponse("partials/x_result.html", context)
    return templates.TemplateResponse("predict.html", context)

# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=8001)
