# quizzes/views.py

import logging
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.exceptions import ObjectDoesNotExist
from .models import Quiz, Question, Choice, QuizAttempt, QuizResponse
from .serializers import QuizSerializer, QuestionSerializer, ChoiceSerializer, QuizAttemptSerializer, QuizResponseSerializer
from django.utils import timezone
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        logger.info(f"User {request.user.username} requested all quizzes")
        try:
            quizzes = self.get_queryset()
            serializer = self.get_serializer(quizzes, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving quizzes: {str(e)}")
            return Response({"error": "An error occurred while retrieving quizzes"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        logger.info(f"User {request.user.username} requested questions for quiz {pk}")
        try:
            quiz = self.get_object()
            logger.debug(f"Quiz object retrieved: {quiz}")
            questions = quiz.questions.all()
            logger.debug(f"Number of questions retrieved: {questions.count()}")
            serializer = QuestionSerializer(questions, many=True)
            logger.debug(f"Questions serialized. Data: {serializer.data}")
            response = Response(serializer.data)
            logger.info(f"Sending response for quiz {pk} questions. Status code: {response.status_code}")
            return response
        except ObjectDoesNotExist:
            logger.warning(f"Quiz {pk} not found")
            return Response({"error": "Quiz not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving questions for quiz {pk}: {str(e)}", exc_info=True)
            return Response({"error": "An error occurred while retrieving questions"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=True, methods=['post'])
    def start_attempt(self, request, pk=None):
        logger.info(f"User {request.user.username} started an attempt for quiz {pk}")
        try:
            quiz = self.get_object()
            attempt = QuizAttempt.objects.create(quiz=quiz, user=request.user)
            serializer = QuizAttemptSerializer(attempt)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist:
            logger.warning(f"Quiz {pk} not found")
            return Response({"error": "Quiz not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error starting attempt for quiz {pk}: {str(e)}")
            return Response({"error": "An error occurred while starting the quiz attempt"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        logger.debug(f"QuestionViewSet dispatch method called. Method: {request.method}, PATH: {request.path}")
        return super().dispatch(request, *args, **kwargs)

    def retrieve(self, request, pk=None):
        logger.info(f"User {request.user.username} requested question {pk}")
        try:
            question = self.get_queryset().get(pk=pk)
            logger.debug(f"Question retrieved: {question}")
            serializer = self.get_serializer(question)
            logger.debug(f"Question serialized. Data: {serializer.data}")
            return Response(serializer.data)
        except Question.DoesNotExist:
            logger.warning(f"Question {pk} not found")
            return Response({"error": "Question not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving question {pk}: {str(e)}", exc_info=True)
            return Response({"error": "An error occurred while retrieving the question"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        logger.info(f"User {request.user.username} is creating a new question")
        try:
            quiz_id = request.data.get('quiz')
            quiz = get_object_or_404(Quiz, id=quiz_id)
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(quiz=quiz)
            logger.info(f"New question created for quiz {quiz_id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist:
            logger.warning(f"Quiz {quiz_id} not found")
            return Response({"error": "Quiz not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error creating question: {str(e)}", exc_info=True)
            return Response({"error": "An error occurred while creating the question"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def choices(self, request, pk=None):
        logger.info(f"User {request.user.username} requested choices for question {pk}")
        try:
            question = self.get_object()
            choices = question.choices.all()
            serializer = ChoiceSerializer(choices, many=True)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            logger.warning(f"Question {pk} not found")
            return Response({"error": "Question not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving choices for question {pk}: {str(e)}")
            return Response({"error": "An error occurred while retrieving choices"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def add_choice(self, request, pk=None):
        logger.info(f"User {request.user.username} is adding a choice to question {pk}")
        try:
            question = self.get_object()
            serializer = ChoiceSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(question=question)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            logger.warning(f"Question {pk} not found")
            return Response({"error": "Question not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error adding choice to question {pk}: {str(e)}")
            return Response({"error": "An error occurred while adding the choice"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ChoiceViewSet(viewsets.ModelViewSet):
    queryset = Choice.objects.all()
    serializer_class = ChoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        logger.info(f"User {request.user.username} requested all choices")
        try:
            choices = self.get_queryset()
            serializer = self.get_serializer(choices, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving choices: {str(e)}")
            return Response({"error": "An error occurred while retrieving choices"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class QuizAttemptViewSet(viewsets.ModelViewSet):
    queryset = QuizAttempt.objects.all()
    serializer_class = QuizAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return QuizAttempt.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def submit_response(self, request, pk=None):
        logger.info(f"User {request.user.username} is submitting a response for attempt {pk}")
        try:
            attempt = self.get_object()
            serializer = QuizResponseSerializer(data=request.data)
            if serializer.is_valid():
                if serializer.validated_data['question'].quiz != attempt.quiz:
                    logger.warning(f"Question does not belong to the current quiz for attempt {pk}")
                    return Response({"error": "This question does not belong to the current quiz."}, status=status.HTTP_400_BAD_REQUEST)
                
                existing_response = QuizResponse.objects.filter(quiz_attempt=attempt, question=serializer.validated_data['question']).first()
                if existing_response:
                    logger.warning(f"Response already submitted for question in attempt {pk}")
                    return Response({"error": "A response for this question has already been submitted."}, status=status.HTTP_400_BAD_REQUEST)
                
                serializer.save(quiz_attempt=attempt)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            logger.warning(f"Attempt {pk} not found")
            return Response({"error": "Attempt not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error submitting response for attempt {pk}: {str(e)}")
            return Response({"error": "An error occurred while submitting the response"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def finish_attempt(self, request, pk=None):
        logger.info(f"User {request.user.username} is finishing attempt {pk}")
        try:
            attempt = self.get_object()
            if attempt.end_time:
                logger.warning(f"Attempt {pk} has already been finished")
                return Response({"error": "This attempt has already been finished."}, status=status.HTTP_400_BAD_REQUEST)
            
            attempt.end_time = timezone.now()
            total_points = sum(question.points for question in attempt.quiz.questions.all())
            earned_points = sum(
                response.question.points
                for response in attempt.responses.all()
                if response.selected_choice and response.selected_choice.is_correct
            )
            attempt.score = (earned_points / total_points) * 100 if total_points > 0 else 0
            attempt.save()
            serializer = QuizAttemptSerializer(attempt)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            logger.warning(f"Attempt {pk} not found")
            return Response({"error": "Attempt not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error finishing attempt {pk}: {str(e)}")
            return Response({"error": "An error occurred while finishing the attempt"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

