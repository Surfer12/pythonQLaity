import click

from cli.commands.analyze import analyze

@click.group()
def cli():
    """Code Sentinel - Static Analysis Tool for Code Quality and Security"""
    pass

cli.add_command(analyze)

if __name__ == '__main__':
    cli()
