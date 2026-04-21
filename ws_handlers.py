from aiohttp import web 
import sys, os, asyncio
from jinja2 import Environment, FileSystemLoader

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'utils')))
from utils.log_config import get_logger
from risk_manager import RiskEngine

logger= get_logger()
#logger.info("main TEST")

template_path= os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
env= Environment(loader=FileSystemLoader(template_path), enable_async=True)



async def landing_page(request:web.Request) -> web.Response:
    global env
    template= env.get_template('dashboard.html')
    rendered_contents= await template.render_async()

    return web.Response(
        text= rendered_contents,
        content_type= "text/html"
    )


    
async def ws_handler(request:web.Request) -> web.WebSocketResponse:
    risk_engine= request.app['risk_engine']
    ws= web.WebSocketResponse()
    await ws.prepare(request)

    logger.info("[WS]: Client is connected to the dashboard")

    try:
        while True:
            metrics= risk_engine.calculate_metrics()
            #print("METRICS ARE CALCULATED")

            #await ws.send_json(metrics.to_json())
            await ws.send_str(metrics.to_json())

            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"[WS]: Connection is closed: {e}")

    finally:
        return ws
    


async def start_aiohttp(risk_engine:RiskEngine):
    try:
        application= web.Application()
        # Store the risk engine in the app, so the handler can see it
        application['risk_engine']= risk_engine
        application.add_routes([
            web.get('/index/', landing_page),
            web.get('/ws/dashboard/', ws_handler)
        ])

        # Use app runner to not block the main loop. We want two servers one brain (event-loop)
        runner= web.AppRunner(application)
        await runner.setup()
        site= web.TCPSite(runner, host="127.0.0.1", port= 8080)
        await site.start()
        logger.info("[WS SERVER]: Dahsboard API is running on http://127.0.0.1:8080")
    except web.CleanupError:
        logger.error(f"[WS SERVER]: Websocket server is closed")
