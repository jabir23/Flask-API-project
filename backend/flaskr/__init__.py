import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def get_pagination(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page-1)* QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions_page = [question.format() for question in selection]
    current_question = questions_page[start:end]

    return current_question



def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
   

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app, resources={r"/api/*":{"origins":"*"} })
    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers','Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Headers','GET, POST, PATCH, DELETE, OPTIONS')
        return response
   
    
    #categories 
    @app.route('/categories')
    def get_categories():
        categories= Category.query.order_by(Category.id).all()
        if len(categories)==0:
            abort(404)

        return jsonify({
            'success':True,
            'categories':{cat.id:cat.type for cat in categories}
        }),200
            

    
    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route('/questions', methods=['GET'])
    def return_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = get_pagination(request, selection)

        categories = Category.query.order_by(Category.type).all()
        formatted_categories = {
            category.id: category.type for category in categories
        }

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'categories': formatted_categories,
        }), 200


    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route('/api/questions/<int:questions_id>', methods=['DELETE'])
    def delete_question(questions_id):
        try:
            del_question = Question.query.filter(Question.id==questions_id).one_or_none()
            if del_question is None:
                abort(404)

            del_question.delete()
            selection = Question.query.order_by(Question.id).all()
            remaining_questions = get_pagination(request, selection)
            
            return jsonify({
                'success':True,
                'deleted': del_question,
                'questions': remaining_questions,
                'total_questions': len(Question.query.all())
        })
        except:
            abort(422)



    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route('/api/questions', methods=["POST"])
    def post_questions():
        body = request.get_json()

        question = body.get("question", None)
        answer = body.get("answer", None)
        difficulty = int(body.get("difficulty", None))
        category = int(body.get("category", None))

        #to insure difficulty is from 1 to 5
        if not 0 < int(difficulty) < 6:
            abort(400)

        try:
            question = Question(question=question, answer=answer, category=category, difficulty=difficulty)
            question.insert()

            selection = Question.query.order_by(Question.id).all()
            current_questions = get_pagination(request, selection)

            return jsonify(
                {
                    "success": True,
                    "created": question.id,
                    "books": current_questions,
                    "total_books": len(Question.query.all()),
                }
            )

        except:
            abort(422)


    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route('/api/questions/search', methods=['POST'])
    def question_search():
        search_term = request.get_json.get('searchTerm')
        if search_term:
            search_results = Question.query.filter(Question.question.ilike(f"%{search_term}%")).all()

            if len(search_results) == 0:
                abort(404)

            return jsonify({
                'success': True,
                'questions': [question.format() for question in search_results],
                'total_questions': len(search_results),
            }), 200
        else:
            abort(400)
    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route('/api/questions/categories/<int:id>/questions', methods=['GET'])
    def return_q_with_id(id):
        category = Category.query.filter(Category.id).one_or_none()
        questions = Question.query.filter(Question.category==id).all()

        current_questions = [q_id.format() for q_id in questions]
        
        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            "questions": current_questions,
            "total_questions": len(Question.query.all()),
            "current_category": category.format()
            })  


    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/api/quizzes', methods=['POST'])
    def quiz():
        try:
            body = request.get_json()
            previous_questions = body.get('previous_questions')
            quiz_category = body.get('quiz_category')
            if int(quiz_category['id']) == 0:
                questions = Question.query.all()
            else:  
                questions = Question.query.filter(Question.category == quiz_category['id']).all()
            formated_questions = [q.format() for q in questions]
            if len(questions) == 0:
                abort(404)
            question = random.choice(formated_questions)
            while 1:
                if int(question['id']) in previous_questions:
                    question = random.choice(formated_questions)
                else:
                    break  
                
            return jsonify({
                'question':question,
                'total_questions':len(Question.query.all())
                })
        except:
            return abort(422)  

    @app.errorhandler(404)
    def page_not_found(error):
        return jsonify({
            'Success': False,
            'error':404,
            'message':'Resources not found'
        }), 404
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'Success': False,
            'error':400,
            'message':'Bad request'
        }), 400

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            'Success': False,
            'error':422,
            'message':'unprocessable'
        }), 422

    @app.errorhandler(500)
    def unprocessable(error):
        return jsonify({
            'Success': False,
            'error':404,
            'message':'Bad Request'
        }), 404


    return app   


  
