"""
Command line interface for prolix
"""
import click
import colorama

from prolix.core import QuizRun, CardRun

colorama.init()


@click.group()
def dispatch_cli():
    pass


@dispatch_cli.command()
@click.option('-n', '--name', 'name', default=None, help='name of user')
@click.option('-q', '--questions', 'question_count', default=15,
              help='number of questions in the quiz')
@click.option('-d', '--definitions', 'def_count', default=4,
              help='number of definitions')
@click.option('-o', '--on', 'quiz_on', default='word',
              help='quiz on word or definition')
def quiz(name=None, question_count=15, def_count=4, quiz_on='word'):
    """
    Quiz the user.
    """
    quiz_run = QuizRun(question_count=question_count, user=name,
                       choice_count=def_count, quiz_on=quiz_on)
    quiz_run()


on_help = 'indicates if the cards should start on the word or definition side'


@dispatch_cli.command()
@click.option('-n', '--name', 'name', default=None, help='name of user')
@click.option('-o', '--on', 'start_on', default='word', help=on_help)
def cards(name=None, start_on='word'):
    """
    Show the user the flash cards.

    Parameters
    ----------
    name
    start_on

    Returns
    -------

    """
    card_run = CardRun(start_on=start_on, user=name)
    card_run()
