def main_cli() -> None:
    parser = argparse.ArgumentParser(description="VTK/Web Multi-Session Contour Filter web-application")
    server.add_arguments(parser)
    args = parser.parse_args()
    Middleware.authKey = args.authKey
    server.start_webserver(options=args, protocol=Middleware)
