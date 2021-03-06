from flask import Flask, render_template, request, redirect, session
import data_manager
import os
import util
import bcrypt
from datetime import timedelta

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/upload'
app.secret_key = "super secret key"
app.permanent_session_lifetime = timedelta(days=5)

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
def list_5_questions():
    order_by = request.args.get(ORDER_BY, 'submission_time')
    order_dir = request.args.get(ORDER_DIR, 'descending')

    logged_in = False
    if 'logged-user' in session:
        logged_in = True

    if order_by in ORDER_BY_LABELS:
        order_dir_sql = ORDER_DIR_SQL[order_dir]
        users_questions = data_manager.get_5_questions_sorted(order_by, order_dir_sql)

        return render_template('list.html',
                               questions=users_questions,
                               order_by_labels=ORDER_BY_LABELS,
                               order_dir_labels=ORDER_DIR_LABELS,
                               current_order_by=order_by,
                               current_order_dir=order_dir,
                               logged_in=logged_in)

    return redirect("/")


@app.route("/list")
def list_questions():
    order_by = request.args.get(ORDER_BY, 'submission_time')
    order_dir = request.args.get(ORDER_DIR, 'descending')

    logged_in = False
    if 'logged-user' in session:
        logged_in = True

    if order_by in ORDER_BY_LABELS:
        order_dir_sql = ORDER_DIR_SQL[order_dir]
        users_questions = data_manager.get_all_questions_sorted(order_by, order_dir_sql)

        return render_template('list.html',
                               questions=users_questions,
                               order_by_labels=ORDER_BY_LABELS,
                               order_dir_labels=ORDER_DIR_LABELS,
                               current_order_by=order_by,
                               current_order_dir=order_dir,
                               logged_in=logged_in)

    return redirect("/list")


@app.route("/question/<int:question_id>", methods=["GET"])
def display_question(question_id):
    data_manager.update_view_number(question_id)
    selected_question = data_manager.get_question_by_id(question_id)
    answers_for_question = data_manager.get_answers_for_question(question_id)
    comments_for_question = data_manager.get_comments_for_question(question_id)

    if len(answers_for_question) != 0:
        comments_for_answers = []
        for element in answers_for_question:
            comments_for_answer = data_manager.get_comments_for_answer(element['id'])
            comments_for_answers.append(comments_for_answer)

    else:
        comments_for_answers = []

    return render_template('display_question.html',
                           question=selected_question,
                           answers=answers_for_question,
                           question_comments=comments_for_question,
                           answers_comments=comments_for_answers)


@app.route("/add-question", methods=["GET"])
def add_question():
    return render_template('add_question.html')


@app.route("/add-question", methods=["POST"])
def add_new_question_post():
    submission_time = util.get_actual_date()
    question_title = request.form['new_question']
    question_description = request.form['question_description']

    path = save_image_to_file(request.files)

    new_table_row = [submission_time, '0', '0', question_title, question_description, path]
    question_id = data_manager.save_question_to_table(new_table_row)

    return redirect(f'/question/{question_id}')


@app.route("/question/<int:question_id>/delete", methods=["GET"])
def delete_question(question_id):
    data_manager.delete_question(question_id)
    # data_manager.delete_answers_to_questions(question_id)

    return redirect("/")


@app.route("/question/<int:question_id>/edit", methods=["GET"])
def edit_question(question_id):
    question_to_edit = data_manager.get_question_by_id(question_id)
    return render_template('edit_question.html', question=question_to_edit)


@app.route("/question/<int:question_id>/edit", methods=["POST"])
def edit_question_post(question_id):
    title = request.form['edited_question']
    message = request.form['edited_description']

    path = None
    if request.files:
        path = save_image_to_file(request.files)

    data_manager.edit_question(question_id, title, message, path)

    return redirect(f'/question/{question_id}')


@app.route("/question/<int:question_id>/new-comment", methods=["GET"])
def add_new_comment_to_question(question_id):
    selected_question = data_manager.get_question_by_id(question_id)

    return render_template('comment_to_question.html', question=selected_question)


@app.route("/question/<int:question_id>/new-comment", methods=["POST"])
def add_new_comment_to_question_post(question_id):
    comment = request.form['comment']
    submission_time = util.get_actual_date()
    new_table_row = [question_id, None, comment, submission_time, None]
    data_manager.save_comment_to_table(new_table_row)

    return redirect(f'/question/{question_id}')


@app.route("/question/<int:question_id>/new-answer", methods=["GET"])
def add_new_answer(question_id):
    question_to_answer = data_manager.get_question_by_id(question_id)
    return render_template('answer.html', question=question_to_answer)


@app.route("/question/<int:question_id>/new-answer", methods=["POST"])
def add_new_answer_post(question_id):
    submission_time = util.get_actual_date()
    message = request.form['answer_description']

    path = save_image_to_file(request.files)

    new_table_row = [submission_time, '0', question_id, message, path]
    data_manager.save_answer_to_table(new_table_row)

    return redirect(f'/question/{question_id}')


@app.route("/answer/<int:answer_id>/delete", methods=["GET"])
def delete_answer(answer_id):
    question_id = request.args.get('question_id')
    data_manager.delete_answer_in_database(answer_id)

    return redirect(f'/question/{question_id}')


@app.route("/comments/<int:comment_id>/delete", methods=["GET"])
def delete_question_comment(comment_id):
    question_id = request.args.get('question_id')
    data_manager.delete_comment_in_database(comment_id)

    return redirect(f'/question/{question_id}')


@app.route("/answer/<int:answer_id>/edit", methods=["GET"])
def edit_answer(answer_id):
    answer_to_edit = data_manager.get_answer_by_id(answer_id)
    return render_template('edit_answer.html', answer=answer_to_edit)


@app.route("/answer/<int:answer_id>/edit", methods=["POST"])
def edit_answer_post(answer_id):
    message = request.form['edit_answer_message']

    if request.files:
        path = save_image_to_file(request.files)

    question_id = data_manager.edit_answer(answer_id, message, path)

    return redirect(f'/question/{question_id}')


@app.route("/comment/<int:comment_id>/edit", methods=["GET"])
def edit_question_comment(comment_id):
    comment_to_edit = data_manager.get_comment_by_id(comment_id)
    question = data_manager.get_question_by_id(comment_to_edit['question_id'])
    return render_template('edit_comment_to_question.html', comment=comment_to_edit, question=question)


@app.route("/comment/<int:comment_id>/edit", methods=["POST"])
def edit_question_comment_post(comment_id):
    message = request.form['edit_comment_message']
    question_id = data_manager.edit_comment_in_database(comment_id, message)

    return redirect(f'/question/{question_id}')


@app.route("/answer/<answer_id>/new-comment", methods=["GET"])
def add_comment_to_answer(answer_id):
    selected_answer = data_manager.get_answer_by_id(answer_id)

    return render_template('comment_to_answer.html', answer=selected_answer)


@app.route("/answer/<answer_id>/new-comment", methods=["POST"])
def add_comment_to_answer_post(answer_id):
    comment = request.form['answer_comment']
    submission_time = util.get_actual_date()
    new_table_row = [None, answer_id, comment, submission_time, None]
    data_manager.save_comment_to_table(new_table_row)
    question = data_manager.get_question_id_by_answer_id(answer_id)

    return redirect(f'/question/{question["question_id"]}')


@app.route("/answer_comment/<int:comment_id>/edit", methods=["GET"])
def edit_answer_comment(comment_id):
    comment_to_edit = data_manager.get_comment_by_id(comment_id)
    answer = data_manager.get_answer_by_id(comment_to_edit['answer_id'])

    return render_template('edit_comment_to_answer.html',
                           comment=comment_to_edit,
                           answer=answer)


@app.route("/answer_comment/<int:comment_id>/edit", methods=["POST"])
def edit_answer_comment_post(comment_id):
    message = request.form['edit_comment_message']
    question_id = data_manager.edit_comment_in_database(comment_id, message)

    return redirect(f'/question/{question_id}')


@app.route("/question/<int:question_id>/vote_up", methods=["GET"])
def up_vote_question(question_id):
    data_manager.update_question_vote_number(question_id, '+')

    return redirect('/list')


@app.route("/question/<int:question_id>/vote_down", methods=["GET"])
def down_vote_question(question_id):
    data_manager.update_question_vote_number(question_id, '-')

    return redirect('/list')


@app.route("/question/<int:question_id>/<int:answer_id>/vote_up", methods=["GET"])
def up_vote_answer(question_id, answer_id):
    data_manager.update_answer_vote_number(answer_id, '+')

    return redirect(f'/question/{question_id}')


@app.route("/question/<int:question_id>/<int:answer_id>/vote_down", methods=["GET"])
def down_vote_answer(question_id, answer_id):
    data_manager.update_answer_vote_number(answer_id, '-')

    return redirect(f'/question/{question_id}')


def save_image_to_file(files):
    try:  # saving image to file
        if 'image' in files:
            file1 = request.files['image']
            path = os.path.join(app.config['UPLOAD_FOLDER'], file1.filename)
            file1.save(path)
            return path

    except OSError:
        pass


@app.route("/search", methods=["GET"])
def search_questions():
    phrase = '%'+request.args.get('q')+'%'

    search_results = data_manager.get_questions_by_search(phrase)

    return render_template('list.html',
                           questions=search_results,
                           order_by_labels=ORDER_BY_LABELS,
                           order_dir_labels=ORDER_DIR_LABELS,
                           current_order_by='submission_time',
                           current_order_dir='descending')


@app.route("/login", methods=["GET"])
def login():
    if 'logged-user' in session:
        redirect('/')
    return render_template('login.html', invalid='False')


@app.route("/login", methods=["POST"])
def login_post():
    if request.form.get('perm_session') == 'on':
        session.permanent = True

    email = request.form.get('email')
    password = request.form.get('password')
    user_details = data_manager.get_user_details(email)
    print(user_details)

    if user_details:
        hashed_pass = bytes.fromhex(user_details['h_password'])

        if bcrypt.checkpw(password.encode('utf-8'), hashed_pass):
            session['logged-user'] = user_details['username']
            return redirect('/')
        else:
            return render_template('login.html', invalid=True)
    else:
        return render_template('login.html', invalid=True)


@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect('/')


@app.route("/register", methods=["GET"])
def register():
    return render_template('register.html', missmatch='False')


@app.route("/register", methods=["POST"])
def register_post():
    password = request.form.get('password')
    c_password = request.form.get('c_password')
    if password == c_password:
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        hashed_pass_hex = hashed_pw.hex()
        reg_time = util.get_actual_date()
        username = request.form.get('username')
        email = request.form.get('email')
        data_manager.create_new_user(username, email, hashed_pass_hex, reg_time)
        return redirect('/login')
    else:
        return render_template('register.html', missmatch=True)


if __name__ == "__main__":
    app.run(debug=True)
