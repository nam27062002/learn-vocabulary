#!/usr/bin/env python
"""
Simple script to check statistics issues
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learn_english_project.settings')
django.setup()

from django.contrib.auth.models import User
from vocabulary.models import StudySession, StudySessionAnswer, DailyStatistics
from vocabulary.statistics_utils import get_user_statistics_summary
from django.db.models import Sum, Count
from datetime import timedelta
from django.utils import timezone

def check_user_statistics(username):
    try:
        user = User.objects.get(username=username)
        print(f"Checking statistics for user: {user.username}")
        print("=" * 50)
        
        # 1. Check recent study sessions
        print("\n1. RECENT STUDY SESSIONS:")
        recent_sessions = StudySession.objects.filter(user=user).order_by('-session_start')[:10]
        print(f"Recent sessions count: {recent_sessions.count()}")
        
        total_questions_from_sessions = 0
        for session in recent_sessions:
            total_questions_from_sessions += session.total_questions
            print(f"  Session {session.id}: {session.total_questions} questions, {session.session_start}")
        
        print(f"Total questions from recent sessions: {total_questions_from_sessions}")
        
        # 2. Check all sessions
        print("\n2. ALL STUDY SESSIONS:")
        all_sessions = StudySession.objects.filter(user=user)
        total_sessions = all_sessions.count()
        total_questions_all = all_sessions.aggregate(total=Sum('total_questions'))['total'] or 0
        
        print(f"Total sessions: {total_sessions}")
        print(f"Total questions from all sessions: {total_questions_all}")
        
        # 3. Check sessions with high question counts
        print("\n3. SESSIONS WITH HIGH QUESTION COUNTS:")
        high_sessions = all_sessions.filter(total_questions__gt=100).order_by('-total_questions')
        print(f"Sessions with >100 questions: {high_sessions.count()}")
        
        for session in high_sessions[:5]:
            actual_answers = StudySessionAnswer.objects.filter(session=session).count()
            print(f"  Session {session.id}: {session.total_questions} questions (actual answers: {actual_answers})")
            print(f"    Start: {session.session_start}, End: {session.session_end}")
            print(f"    Duration: {session.session_duration_seconds}s")
        
        # 4. Check StudySessionAnswer records
        print("\n4. STUDY SESSION ANSWERS:")
        all_answers = StudySessionAnswer.objects.filter(session__user=user)
        total_answers = all_answers.count()
        print(f"Total StudySessionAnswer records: {total_answers}")
        
        # 5. Check DailyStatistics
        print("\n5. DAILY STATISTICS:")
        daily_stats = DailyStatistics.objects.filter(user=user)
        total_daily_questions = daily_stats.aggregate(total=Sum('total_questions_answered'))['total'] or 0
        print(f"Total questions from daily stats: {total_daily_questions}")
        
        # 6. Check current statistics summary
        print("\n6. CURRENT STATISTICS SUMMARY (30 days):")
        stats = get_user_statistics_summary(user, 30)
        print(f"Questions answered: {stats['total_questions_answered']}")
        print(f"Correct answers: {stats['correct_answers']}")
        print(f"Incorrect answers: {stats['incorrect_answers']}")
        print(f"Accuracy: {stats['accuracy_percentage']}%")
        
        # 7. Check for potential issues
        print("\n7. POTENTIAL ISSUES:")
        if total_questions_all != total_answers:
            print(f"❌ MISMATCH: Session totals ({total_questions_all}) != Answer records ({total_answers})")
        else:
            print("✅ Session totals match answer records")
            
        if total_daily_questions != total_questions_all:
            print(f"❌ MISMATCH: Daily stats ({total_daily_questions}) != Session totals ({total_questions_all})")
        else:
            print("✅ Daily stats match session totals")
            
        # 8. Check for duplicate answers
        print("\n8. DUPLICATE ANSWER CHECK:")
        duplicate_answers = all_answers.values(
            'session', 'flashcard'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        if duplicate_answers.exists():
            print(f"❌ Found {duplicate_answers.count()} potential duplicate answer groups")
            for dup in duplicate_answers[:5]:
                print(f"  Session {dup['session']}, Card {dup['flashcard']}: {dup['count']} records")
        else:
            print("✅ No duplicate answers found")
            
        # 9. Check incomplete sessions
        print("\n9. INCOMPLETE SESSIONS:")
        incomplete_sessions = all_sessions.filter(session_end__isnull=True)
        if incomplete_sessions.exists():
            print(f"❌ Found {incomplete_sessions.count()} incomplete sessions")
            for session in incomplete_sessions[:5]:
                print(f"  Session {session.id}: {session.total_questions} questions, started {session.session_start}")
        else:
            print("✅ No incomplete sessions found")
            
    except User.DoesNotExist:
        print(f"User '{username}' not found")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else 'nam27062002'
    check_user_statistics(username)
