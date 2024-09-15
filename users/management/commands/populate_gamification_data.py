# gamification/management/commands/populate_gamification_data.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from gamification.models import (
    UserGamificationProfile,
    Badge,
    UserBadge,
    Achievement,
    UserAchievement,
    GamificationAction,
    UserAction,
    Level,
    Quest,
    QuestTask,
    UserQuest,
    Reward,
    UserReward
)
import random
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with sample gamification data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample gamification data...')

        # Create sample users if they don't exist
        users = self.create_sample_users()

        # Create badges
        badges = self.create_badges()

        # Create achievements
        achievements = self.create_achievements(badges)

        # Create gamification actions
        actions = self.create_gamification_actions()

        # Create levels
        levels = self.create_levels(badges)

        # Create quests
        quests = self.create_quests(badges, actions)

        # Create rewards
        rewards = self.create_rewards()

        # Create user gamification profiles and assign random data
        self.create_user_data(users, badges, achievements, actions, quests, rewards)

        self.stdout.write(self.style.SUCCESS('Successfully created sample gamification data'))

    def create_sample_users(self):
        users = []
        for i in range(1, 6):
            username = f'user{i}'
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created user: {username}')
            users.append(user)
        return users

    def create_badges(self):
        badges = []
        badge_data = [
            ('Novice', 'Completed your first course', 100),
            ('Expert', 'Completed 10 courses', 1000),
            ('Socializer', 'Made 50 forum posts', 500),
            ('Quiz Master', 'Aced 5 quizzes', 750),
            ('Streak Champion', 'Maintained a 30-day streak', 1500),
        ]
        for name, description, xp_value in badge_data:
            badge, created = Badge.objects.get_or_create(
                name=name,
                defaults={'description': description, 'xp_value': xp_value}
            )
            badges.append(badge)
            if created:
                self.stdout.write(f'Created badge: {name}')
        return badges

    def create_achievements(self, badges):
        achievements = []
        achievement_data = [
            ('First Steps', 'Complete your first course', 500, badges[0]),
            ('Knowledge Seeker', 'Complete 5 courses', 2500, badges[1]),
            ('Community Pillar', 'Make 100 forum posts', 1000, badges[2]),
            ('Quiz Prodigy', 'Ace 10 quizzes', 1500, badges[3]),
            ('Dedicated Learner', 'Maintain a 60-day streak', 3000, badges[4]),
        ]
        for name, description, xp_reward, badge in achievement_data:
            achievement, created = Achievement.objects.get_or_create(
                name=name,
                defaults={'description': description, 'xp_reward': xp_reward, 'badge': badge}
            )
            achievements.append(achievement)
            if created:
                self.stdout.write(f'Created achievement: {name}')
        return achievements

    def create_gamification_actions(self):
        actions = []
        action_data = [
            ('Course Completion', 'COURSE_COMPLETION', 1000, 0, 0),
            ('Resource Completion', 'RESOURCE_COMPLETION', 50, 0, 10),
            ('Quiz Completion', 'QUIZ_COMPLETION', 200, 0, 5),
            ('Daily Login', 'DAILY_LOGIN', 10, 1440, 1),
            ('Forum Post', 'FORUM_POST', 20, 5, 10),
        ]
        for name, action_type, xp_reward, cooldown_minutes, daily_limit in action_data:
            action, created = GamificationAction.objects.get_or_create(
                name=name,
                defaults={
                    'action_type': action_type,
                    'xp_reward': xp_reward,
                    'cooldown_minutes': cooldown_minutes,
                    'daily_limit': daily_limit
                }
            )
            actions.append(action)
            if created:
                self.stdout.write(f'Created gamification action: {name}')
        return actions

    def create_levels(self, badges):
        levels = []
        level_data = [
            (1, 'Beginner', 0, badges[0]),
            (2, 'Intermediate', 1000, None),
            (3, 'Advanced', 3000, badges[1]),
            (4, 'Expert', 6000, None),
            (5, 'Master', 10000, badges[4]),
        ]
        for number, name, xp_threshold, badge in level_data:
            level, created = Level.objects.get_or_create(
                number=number,
                defaults={'name': name, 'xp_threshold': xp_threshold, 'badge': badge}
            )
            levels.append(level)
            if created:
                self.stdout.write(f'Created level: {name}')
        return levels

    def create_quests(self, badges, actions):
        quests = []
        quest_data = [
            ('Weekly Challenge', 'Complete 3 courses this week', 1000, badges[0], 3),
            ('Forum Contributor', 'Make 20 forum posts', 500, badges[2], 1),
            ('Quiz Mastery', 'Ace 5 quizzes', 750, badges[3], 2),
        ]
        for name, description, xp_reward, badge_reward, task_count in quest_data:
            quest, created = Quest.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'xp_reward': xp_reward,
                    'badge_reward': badge_reward,
                    'start_date': timezone.now(),
                    'end_date': timezone.now() + timedelta(days=7)
                }
            )
            if created:
                self.stdout.write(f'Created quest: {name}')
                for i in range(task_count):
                    QuestTask.objects.create(
                        quest=quest,
                        action=random.choice(actions),
                        required_count=random.randint(1, 5),
                        order=i+1
                    )
            quests.append(quest)
        return quests

    def create_rewards(self):
        rewards = []
        reward_data = [
            ('Course Discount', 'Get 20% off on your next course purchase', 5000),
            ('Premium Content', 'Unlock exclusive learning materials', 3000),
            ('One-on-One Tutoring', '30-minute session with an expert', 10000),
            ('Certificate Frame', 'Digital frame for your certificates', 2000),
            ('Profile Badge', 'Exclusive profile badge', 1500),
        ]
        for name, description, xp_cost in reward_data:
            reward, created = Reward.objects.get_or_create(
                name=name,
                defaults={'description': description, 'xp_cost': xp_cost}
            )
            rewards.append(reward)
            if created:
                self.stdout.write(f'Created reward: {name}')
        return rewards

    def create_user_data(self, users, badges, achievements, actions, quests, rewards):
        for user in users:
            # Create or update user gamification profile
            profile, created = UserGamificationProfile.objects.get_or_create(
                user=user,
                defaults={
                    'xp': random.randint(0, 10000),
                    'level': random.randint(1, 5),
                    'streak_days': random.randint(0, 30),
                    'last_activity_date': timezone.now() - timedelta(days=random.randint(0, 10))
                }
            )
            if created:
                self.stdout.write(f'Created gamification profile for user: {user.username}')

            # Assign random badges
            for badge in random.sample(badges, k=random.randint(1, len(badges))):
                UserBadge.objects.get_or_create(user=user, badge=badge)

            # Assign random achievements
            for achievement in random.sample(achievements, k=random.randint(1, len(achievements))):
                UserAchievement.objects.get_or_create(user=user, achievement=achievement)

            # Create random user actions
            for _ in range(random.randint(5, 20)):
                action = random.choice(actions)
                UserAction.objects.create(
                    user=user,
                    action=action,
                    performed_at=timezone.now() - timedelta(days=random.randint(0, 30)),
                    xp_earned=action.xp_reward
                )

            # Assign random quests
            for quest in random.sample(quests, k=random.randint(1, len(quests))):
                UserQuest.objects.get_or_create(
                    user=user,
                    quest=quest,
                    defaults={
                        'progress': {},
                        'started_at': timezone.now() - timedelta(days=random.randint(1, 7))
                    }
                )

            # Assign random rewards
            for reward in random.sample(rewards, k=random.randint(0, len(rewards))):
                UserReward.objects.create(
                    user=user,
                    reward=reward,
                    redeemed_at=timezone.now() - timedelta(days=random.randint(0, 30))
                )

        self.stdout.write(f'Created sample data for {len(users)} users')