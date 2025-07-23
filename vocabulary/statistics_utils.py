"""
Utility functions for managing statistics and analytics.
"""
from datetime import datetime, timedelta, date
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from .models import (
    StudySession, StudySessionAnswer, DailyStatistics, 
    WeeklyStatistics, Flashcard, Deck
)


def create_study_session(user, study_mode='deck', deck_ids=None):
    """Create a new study session for the user."""
    session = StudySession.objects.create(
        user=user,
        study_mode=study_mode
    )
    
    if deck_ids and study_mode == 'deck':
        decks = Deck.objects.filter(id__in=deck_ids, user=user)
        session.decks_studied.set(decks)
    
    return session


def record_answer(session, flashcard, is_correct, response_time_seconds, question_type='multiple_choice'):
    """Record an answer within a study session."""
    # Get difficulty before and after
    difficulty_before = flashcard.difficulty_score
    
    # Create the answer record
    answer = StudySessionAnswer.objects.create(
        session=session,
        flashcard=flashcard,
        is_correct=is_correct,
        response_time_seconds=response_time_seconds,
        question_type=question_type,
        difficulty_before=difficulty_before,
        difficulty_after=flashcard.difficulty_score  # This will be updated by the SM-2 algorithm
    )
    
    # Update session metrics
    session.total_questions += 1
    if is_correct:
        session.correct_answers += 1
    else:
        session.incorrect_answers += 1
    
    # Update average response time
    if session.total_questions == 1:
        session.average_response_time = response_time_seconds
    else:
        # Calculate running average
        total_time = session.average_response_time * (session.total_questions - 1) + response_time_seconds
        session.average_response_time = total_time / session.total_questions
    
    # Update unique words count
    unique_words = StudySessionAnswer.objects.filter(
        session=session
    ).values('flashcard').distinct().count()
    session.words_studied = unique_words
    
    session.save(update_fields=[
        'total_questions', 'correct_answers', 'incorrect_answers',
        'average_response_time', 'words_studied'
    ])
    
    return answer


def end_study_session(session):
    """End a study session and update statistics."""
    session.end_session()
    
    # Update daily and weekly statistics
    update_daily_statistics(session.user, session.session_start.date())
    update_weekly_statistics(session.user, session.session_start.date())
    
    return session


def update_daily_statistics(user, target_date):
    """Update or create daily statistics for a user and date."""
    daily_stat, created = DailyStatistics.objects.get_or_create(
        user=user,
        date=target_date,
        defaults={
            'is_study_day': False,
            'total_study_time_seconds': 0,
            'total_questions_answered': 0,
            'correct_answers': 0,
            'incorrect_answers': 0,
            'unique_words_studied': 0,
            'study_sessions_count': 0,
            'average_session_duration': 0.0,
            'new_cards_created': 0,
        }
    )
    
    # Get all sessions for this day
    sessions = StudySession.objects.filter(
        user=user,
        session_start__date=target_date,
        session_end__isnull=False  # Only completed sessions
    )
    
    if sessions.exists():
        # Aggregate session data
        session_stats = sessions.aggregate(
            total_time=Sum('session_duration_seconds'),
            total_questions=Sum('total_questions'),
            total_correct=Sum('correct_answers'),
            total_incorrect=Sum('incorrect_answers'),
            session_count=Count('id'),
            avg_duration=Avg('session_duration_seconds'),
            unique_words=Count('answers__flashcard', distinct=True)
        )
        
        # Count new cards created on this day
        new_cards = Flashcard.objects.filter(
            user=user,
            created_at__date=target_date
        ).count()
        
        # Update daily statistics
        daily_stat.is_study_day = True
        daily_stat.total_study_time_seconds = session_stats['total_time'] or 0
        daily_stat.total_questions_answered = session_stats['total_questions'] or 0
        daily_stat.correct_answers = session_stats['total_correct'] or 0
        daily_stat.incorrect_answers = session_stats['total_incorrect'] or 0
        daily_stat.unique_words_studied = session_stats['unique_words'] or 0
        daily_stat.study_sessions_count = session_stats['session_count'] or 0
        daily_stat.average_session_duration = session_stats['avg_duration'] or 0.0
        daily_stat.new_cards_created = new_cards
        
        daily_stat.save()
    
    return daily_stat


def update_weekly_statistics(user, target_date):
    """Update or create weekly statistics for a user and date."""
    # Get ISO week info
    year, week_number, _ = target_date.isocalendar()
    
    # Calculate week start date (Monday)
    days_since_monday = target_date.weekday()
    week_start = target_date - timedelta(days=days_since_monday)
    
    weekly_stat, created = WeeklyStatistics.objects.get_or_create(
        user=user,
        year=year,
        week_number=week_number,
        defaults={
            'week_start_date': week_start,
            'total_study_time_seconds': 0,
            'total_questions_answered': 0,
            'correct_answers': 0,
            'incorrect_answers': 0,
            'unique_words_studied': 0,
            'study_sessions_count': 0,
            'study_days_count': 0,
            'new_cards_created': 0,
            'weekly_goal_met': False,
        }
    )
    
    # Get all daily stats for this week
    week_end = week_start + timedelta(days=6)
    daily_stats = DailyStatistics.objects.filter(
        user=user,
        date__range=[week_start, week_end]
    )
    
    if daily_stats.exists():
        # Aggregate daily data
        week_stats = daily_stats.aggregate(
            total_time=Sum('total_study_time_seconds'),
            total_questions=Sum('total_questions_answered'),
            total_correct=Sum('correct_answers'),
            total_incorrect=Sum('incorrect_answers'),
            total_sessions=Sum('study_sessions_count'),
            study_days=Count('id', filter=Q(is_study_day=True)),
            unique_words=Sum('unique_words_studied'),
            new_cards=Sum('new_cards_created')
        )
        
        # Update weekly statistics
        weekly_stat.total_study_time_seconds = week_stats['total_time'] or 0
        weekly_stat.total_questions_answered = week_stats['total_questions'] or 0
        weekly_stat.correct_answers = week_stats['total_correct'] or 0
        weekly_stat.incorrect_answers = week_stats['total_incorrect'] or 0
        weekly_stat.study_sessions_count = week_stats['total_sessions'] or 0
        weekly_stat.study_days_count = week_stats['study_days'] or 0
        weekly_stat.unique_words_studied = week_stats['unique_words'] or 0
        weekly_stat.new_cards_created = week_stats['new_cards'] or 0
        
        # Check if weekly goal is met (example: 5 study days or 100 questions)
        weekly_stat.weekly_goal_met = (
            weekly_stat.study_days_count >= 5 or 
            weekly_stat.total_questions_answered >= 100
        )
        
        weekly_stat.save()
    
    return weekly_stat


def get_study_streak(user, end_date=None):
    """Calculate the current study streak for a user."""
    if end_date is None:
        end_date = timezone.now().date()
    
    streak = 0
    current_date = end_date
    
    while True:
        try:
            daily_stat = DailyStatistics.objects.get(user=user, date=current_date)
            if daily_stat.is_study_day:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        except DailyStatistics.DoesNotExist:
            break
    
    return streak


def get_user_statistics_summary(user, days=30):
    """Get a comprehensive statistics summary for a user."""
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    # Get daily stats for the period
    daily_stats = DailyStatistics.objects.filter(
        user=user,
        date__range=[start_date, end_date]
    )
    
    # Aggregate data
    summary = daily_stats.aggregate(
        total_study_time=Sum('total_study_time_seconds'),
        total_questions=Sum('total_questions_answered'),
        total_correct=Sum('correct_answers'),
        total_incorrect=Sum('incorrect_answers'),
        total_sessions=Sum('study_sessions_count'),
        study_days=Count('id', filter=Q(is_study_day=True)),
        unique_words=Sum('unique_words_studied'),
        new_cards=Sum('new_cards_created')
    )
    
    # Calculate additional metrics
    total_cards = Flashcard.objects.filter(user=user).count()
    current_streak = get_study_streak(user)
    
    # Calculate averages
    study_days_count = summary['study_days'] or 0
    avg_daily_questions = (summary['total_questions'] or 0) / study_days_count if study_days_count > 0 else 0
    avg_daily_time = (summary['total_study_time'] or 0) / study_days_count if study_days_count > 0 else 0
    
    accuracy = 0
    if summary['total_questions'] and summary['total_questions'] > 0:
        accuracy = (summary['total_correct'] or 0) / summary['total_questions'] * 100
    
    # Calculate formatted time values
    total_time_seconds = summary['total_study_time'] or 0
    total_time_hours = round(total_time_seconds / 3600, 1) if total_time_seconds > 0 else 0

    return {
        'period_days': days,
        'total_study_time_seconds': total_time_seconds,
        'total_study_time_hours': total_time_hours,
        'total_questions_answered': summary['total_questions'] or 0,
        'correct_answers': summary['total_correct'] or 0,
        'incorrect_answers': summary['total_incorrect'] or 0,
        'accuracy_percentage': round(accuracy, 1),
        'study_sessions_count': summary['total_sessions'] or 0,
        'study_days_count': study_days_count,
        'unique_words_studied': summary['unique_words'] or 0,
        'new_cards_created': summary['new_cards'] or 0,
        'total_cards': total_cards,
        'current_streak': current_streak,
        'avg_daily_questions': round(avg_daily_questions, 1),
        'avg_daily_time_seconds': round(avg_daily_time, 1),
        'consistency_percentage': round((study_days_count / days) * 100, 1),
    }
