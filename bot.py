import asyncio
import logging
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from bot import SmartAIO, dp, SmartPyro, SmartUserBot
from bot.core.database import SmartReboot
from bot.helpers.logger import LOGGER
from bot.misc.callback import handle_callback_query
from importlib import import_module

# Health check server for Render
PORT = int(os.environ.get('PORT', 8080))

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/ping' or self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_HEAD(self):
        """Handle HEAD requests for Render health checks"""
        if self.path == '/ping' or self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress HTTP logs to reduce noise"""
        pass

def run_health_server():
    """Run HTTP server for Render health checks."""
    try:
        server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
        LOGGER.info(f"🌐 Health server started on 0.0.0.0:{PORT}")
        server.serve_forever()
    except Exception as e:
        LOGGER.error(f"Failed to start health server: {e}")

async def main():
    try:
        # Start health check server in a separate thread
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()
        
        modules_path = "bot.modules"
        modules_dir = os.path.join(os.path.dirname(__file__), "bot", "modules")
        for filename in os.listdir(modules_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                try:
                    import_module(f"{modules_path}.{module_name}")
                    LOGGER.info(f"Loaded module: {module_name}")
                except Exception as e:
                    LOGGER.error(f"Failed to load module {module_name}: {e}")
        
        dp.callback_query.register(handle_callback_query)
        
        await SmartPyro.start()
        LOGGER.info("SmartPyro started successfully")
        
        await SmartUserBot.start()
        LOGGER.info("SmartUserBot started successfully")
        
        LOGGER.info("Bot Successfully Started 💥")
        
        restart_data = await SmartReboot.find_one()
        if restart_data:
            try:
                await SmartAIO.edit_message_text(
                    chat_id=restart_data["chat_id"],
                    message_id=restart_data["msg_id"],
                    text="<b>Restarted Successfully 💥</b>",
                    parse_mode="HTML"
                )
                await SmartReboot.delete_one({"_id": restart_data["_id"]})
                
            except Exception as e:
                LOGGER.error(f"Failed to update restart message: {e}")
        
        try:
            await SmartAIO.delete_webhook(drop_pending_updates=True)
            LOGGER.info("Webhook cleared")
        except Exception as e:
            LOGGER.warning(f"Could not clear webhook: {e}")
        
        await asyncio.sleep(1)
        
        await dp.start_polling(
            SmartAIO, 
            drop_pending_updates=True,
            allowed_updates=dp.resolve_used_update_types(),
            handle_signals=False
        )
        
    except asyncio.CancelledError:
        LOGGER.info("Polling cancelled, shutting down...")
        raise
    except Exception as e:
        LOGGER.error(f"Main loop failed: {e}")
        raise

async def cleanup():
    try:
        await SmartPyro.stop()
        LOGGER.info("Terminated SmartPyro session")
    except Exception as e:
        LOGGER.error(f"Failed to stop SmartPyro: {e}")
    
    try:
        await SmartUserBot.stop()
        LOGGER.info("Terminated SmartUserBot session")
    except Exception as e:
        LOGGER.error(f"Failed to stop SmartUserBot: {e}")
    
    try:
        await SmartAIO.session.close()
        LOGGER.info("Closed SmartAIO session")
    except Exception as e:
        LOGGER.error(f"Failed to close SmartAIO session: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Ensure event loop exists for Python 3.14
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        LOGGER.info("Stop signal received. Shutting down...")
        try:
            loop.run_until_complete(cleanup())
        except Exception as e:
            LOGGER.error(f"Failed to terminate sessions: {e}")
        finally:
            if not loop.is_closed():
                loop.close()
