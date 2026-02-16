from os import environ

admob_backend = environ.get('A4K_BACKEND')

match admob_backend:
    case "pyjnius":
        from a4k_pyjnius import AdmobBackend # type: ignore
    case "pyswift":
        from a4k_pyswift import AdmobBackend # type: ignore
    case _:
        raise ValueError(f"Unsupported backend: {admob_backend}. Supported backends: 'android'.")
        
