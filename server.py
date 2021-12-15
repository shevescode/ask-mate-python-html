from flask import Flask, render_template, request, redirect
import data_manager
import time
import util
from datetime import datetime

app = Flask(__name__)

ORDER_BY = 'order_by'
ORDER_BY_LABELS = {'submission_time': 'Time added',
                   'view_number': 'Views',
                   'vote_number': 'Votes',
                   'title': 'Title',
                   'message': 'Message'}

ORDER_DIR = 'order_direction'
ORDER_DIR_LABELS = {'ascending': 'Ascending',
                    'descending': 'Descending'}

ORDER_DIR_SQL = {'ascending': 'ASC',
                 'descending': 'DESC'}


@app.route("/")
@app.route("/list")
def list_questions():
    headers_list = data_manager.get_questions_headers()
    order_by = request.args.get(ORDER_BY, 'submission_time')
    order_dir = request.args.get(ORDER_DIR, 'descending')

    if order_by in ORDER_BY_LABELS:
        order_dir_sql = ORDER_DIR_SQL[order_dir]
        users_questions = data_manager.get_all_questions_sorted(order_by, order_dir_sql)

        return render_template('list.html',
                               questions=users_questions,
                               headers=headers_list,
                               order_by_labels=ORDER_BY_LABELS,
                               order_dir_labels=ORDER_DIR_LABELS,
                               current_order_by=order_by,
                               current_order_dir=order_dir)

    return redirect("/")


@app.route("/question/<question_id>")
def route_display_question(question_id):
    selected_question = data_manager.get_question_by_id(question_id)
    answers_for_question = data_manager.get_answers_for_question(question_id)

    return render_template('display_question.html',
                           question=selected_question, answers=answers_for_question)


@app.route("/add-question", methods=["GET"])
def route_ask_question():
    return render_template('add_question.html')


@app.route("/add-question", methods=["POST"])
def route_create_new_question():
    submission_time = datetime.now()
    question_title = request.form['new_question']
    question_description = request.form['question_description']

    new_table_row = [submission_time, '0', '0', question_title, question_description, 'image']
    data_manager.save_question_to_table(new_table_row)
    question_id = data_manager.get_question_id_by_data(new_table_row)

    return redirect(f'/question/{question_id["id"]}')


@app.route("/question/<question_id>/new-answer", methods=["GET"])
def get_new_answer(question_id):
    question_to_answer = data_manager.get_question_by_id(question_id)
    return render_template('answer.html', question=question_to_answer)


@app.route("/question/<question_id>/new-answer", methods=["POST"])
def route_new_answer(question_id):
    submission_time = datetime.now()
    message = request.form['answer_description']
    new_data_row = [submission_time, '0', question_id, message, 'image']
    data_manager.save_answer_to_table(new_data_row)

    return redirect(f'/question/{question_id}')


@app.route("/question/<question_id>/delete")
def delete_question(question_id):
    users_questions = data_manager.get_all_questions_sorted()
    question_to_delete = util.delete_question(users_questions, question_id)
    data_manager.overwrite_question_in_file(question_to_delete)

    return redirect("/")


@app.route("/question/<question_id>/edit", methods=["POST"])
def edit_question(question_id):
    users_questions = data_manager.get_all_questions_sorted()
    title = request.form['edited_question']
    message = request.form['edited_description']
    table = util.edit_question(users_questions, question_id, title, message)
    data_manager.overwrite_question_in_file(table)

    return redirect(f'/question/{question_id}')


@app.route("/question/<question_id>/edit", methods=["GET"])
def get_edit_question(question_id):
    users_questions = data_manager.get_all_questions_sorted()
    question_to_edit = util.find_question_in_dictionary(users_questions, question_id)
    return render_template('edit_question.html', question=question_to_edit)


if __name__ == "__main__":
    app.run(debug=True)
