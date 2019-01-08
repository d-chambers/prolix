"""
Command line interface for prolix
"""
import click
import colorama

from prolix.core import QuizRun

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
def quiz(name=None, question_count=15, def_count=4):
    """
    Quiz the user.
    """
    quiz_run = QuizRun(question_count=question_count, user=name,
                       definition_count=def_count)
    quiz_run()

    # quiz = prolix.WordQuiz()
    # color_wheel = Wheel(len(quiz.definitions))
    #
    # palette = [
    #     ('title', 'bold', ''),
    #     # ('streak', 'black', 'dark red'),
    #     # ('bg', 'black', 'dark blue'),
    #     ('reversed', 'standout', ''),
    # ]
    #
    #
    #
    # def show_question(title, choices):
    #     title_text = urwid.Text(title.upper(), align='center')
    #     body = [urwid.AttrMap(title_text, 'title'), urwid.Divider()]
    #     for ind, c in enumerate(choices):
    #         button = urwid.Button(c)
    #         urwid.connect_signal(button, 'click', item_chosen, ind)
    #         body.append(urwid.AttrMap(button, None, focus_map='reversed'))
    #         body.append(urwid.Divider())
    #     return urwid.ListBox(urwid.SimpleFocusListWalker(body))
    #
    # def item_chosen(button, choice):
    #     is_correct = quiz.answer(choice)
    #     if is_correct:
    #         pass
    #     else:
    #         pass
    #
    #
    #     breakpoint()
    #
    #     return exit_program(button)
    #     # breakpoint()
    #
    # def exit_program(button):
    #     raise urwid.ExitMainLoop()
    #
    #
    # menu = show_question(quiz.word, quiz.word_def_block)
    # main = urwid.Padding(menu, left=2, right=2)
    # top = urwid.Overlay(main, urwid.SolidFill(u'\N{MEDIUM SHADE}'),
    #                     align='center', width=('relative', 90),
    #                     valign='middle', height=('relative', 60),
    #                     min_width=40, min_height=20)
    # urwid.MainLoop(top, palette=palette).run()
    #
    #

    # def show_or_exit(key):
    #     if key in ('q', 'Q'):
    #         raise urwid.ExitMainLoop()
    #     if key == 'up':
    #         color_wheel.previous()
    #     elif key == 'down':
    #         color_wheel.next()
    #     color = {color_wheel.index: blue}
    #     txt = quiz.gen_string(colors=color)
    #     # breakpoint()
    #     display_txt.set_text(repr(txt))
    #
    # display_txt = urwid.Text(str(quiz))
    # fill = urwid.Filler(display_txt, 'top')
    # loop = urwid.MainLoop(fill, unhandled_input=show_or_exit)
    # loop.run()
