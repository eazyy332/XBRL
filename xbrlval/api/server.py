from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import tempfile
import pathlib
from typing import Optional

from xbrlval.core.validation import ValidationEngine


def create_app(cache_dir: pathlib.Path) -> FastAPI:
    app = FastAPI(title="xbrlval API")
    engine = ValidationEngine(cache_dir=cache_dir)

    @app.post("/validate")
    async def validate_endpoint(
        file: Optional[UploadFile] = File(None),
        url: Optional[str] = Form(None),
        calc: bool = Form(True),
        all_rules: bool = Form(True),
    ):
        if file is None and not url:
            return JSONResponse(status_code=400, content={"error": "Provide 'file' or 'url'"})

        if file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=pathlib.Path(file.filename or "instance.xml").suffix) as tmp:
                data = await file.read()
                tmp.write(data)
                tmp_path = pathlib.Path(tmp.name)
            target = str(tmp_path)
        else:
            target = url  # type: ignore

        report = engine.validate(target, run_calculation=calc, run_all=all_rules)
        return JSONResponse(content=report.to_dict())

    return app


def run_api(host: str, port: int, cache_dir: pathlib.Path) -> None:
    from uvicorn import run

    app = create_app(cache_dir)
    run(app, host=host, port=port)