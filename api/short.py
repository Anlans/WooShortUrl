from fastapi import APIRouter, Depends, BackgroundTasks, status
from fastapi.responses import PlainTextResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies.base import get_db_session
from servies.short import ShortService


router_short = APIRouter(tags=["短链访问"])

@router_short.get("/{short_tag}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def short_redirect(*, short_tag: str,
                         db_session: AsyncSession = Depends(get_db_session),
                         task: BackgroundTasks):
    data = await ShortService.get_short_url(db_session, short_tag)
    if not data:
        raise PlainTextResponse("没有对应的短链信息记录")
    data.visits_count += 1
    task.add_task(ShortService.update_short_url, db_session, short_url_id=data.id, visits_count=data.visits_count)
    return RedirectResponse(url=data.long_url)

