from django.core.management.base import BaseCommand
from courses.models import Program, Course, LearningResource
from django.contrib.auth import get_user_model

User = get_user_model()

# Sample Program Data
programs_data = [
    {
        'title': 'Data Science Fundamentals',
        'description': "This comprehensive program introduces you to the core concepts and tools of data science. You'll learn programming, data analysis, machine learning, and data visualization, preparing you for a career in this exciting field.",
        'short_description': 'Master the essentials of data science with hands-on projects and real-world applications.',
        'program_type': 'INTERNAL',
        'duration': '6 months',
        'level': 'Intermediate',
        'is_published': True
    },
    {
        'title': 'Web Development Bootcamp',
        'description': 'Dive into the world of web development with this intensive bootcamp. Learn front-end and back-end technologies, as well as modern frameworks and tools used in the industry.',
        'short_description': 'Become a full-stack web developer in this comprehensive bootcamp.',
        'program_type': 'INTERNAL',
        'duration': '12 weeks',
        'level': 'Beginner to Intermediate',
        'is_published': True
    },
    {
        'title': 'Cloud Computing Essentials',
        'description': 'Explore the fundamentals of cloud computing and learn how to design, deploy, and manage applications in the cloud. This program covers major cloud platforms and essential concepts.',
        'short_description': 'Master cloud computing concepts and practices.',
        'program_type': 'INTERNAL',
        'duration': '8 weeks',
        'level': 'Intermediate',
        'is_published': True
    },
    {
        'title': 'Artificial Intelligence and Ethics',
        'description': 'Delve into the world of AI while exploring the ethical implications of this powerful technology. Learn about machine learning, neural networks, and the societal impact of AI.',
        'short_description': 'Understand AI technologies and their ethical considerations.',
        'program_type': 'INTERNAL',
        'duration': '10 weeks',
        'level': 'Advanced',
        'is_published': True
    }
]

# Courses within the programs
courses_data = {
    'Data Science Fundamentals': [
        {
            'title': 'Introduction to Python for Data Science',
            'description': 'Learn the basics of Python programming with a focus on data science applications. This course covers data types, control structures, functions, and introduces key libraries like NumPy and Pandas.',
            'short_description': 'Get started with Python for data analysis and manipulation.',
            'duration': '4 weeks',
            'is_published': True
        },
        {
            'title': 'Data Analysis and Visualization',
            'description': 'Dive deep into data analysis techniques and learn to create compelling visualizations. This course covers exploratory data analysis, statistical methods, and uses libraries like Matplotlib and Seaborn.',
            'short_description': 'Analyze and visualize data to derive meaningful insights.',
            'duration': '5 weeks',
            'is_published': True
        },
        {
            'title': 'Machine Learning Fundamentals',
            'description': "Explore the basics of machine learning, including supervised and unsupervised learning techniques. You'll implement algorithms like linear regression, decision trees, and k-means clustering",
            'short_description': 'Understand and apply core machine learning concepts and algorithms.',
            'duration': '6 weeks',
            'is_published': True
        },
        {
            'title': 'Big Data Processing with PySpark',
            'description': 'Learn to process and analyze large-scale datasets using Apache Spark with Python (PySpark). This course covers distributed computing concepts and practical applications in big data scenarios.',
            'short_description': 'Scale your data science skills to handle big data with PySpark.',
            'duration': '5 weeks',
            'is_published': True
        }
    ],
    'Web Development Bootcamp': [
        {
            'title': 'HTML5 and CSS3 Fundamentals',
            'description': 'Learn the building blocks of web development. Master HTML5 for structure and CSS3 for styling to create modern, responsive websites.',
            'short_description': 'Create the foundation of web pages with HTML5 and CSS3.',
            'duration': '2 weeks',
            'is_published': True
        },
        {
            'title': 'JavaScript and DOM Manipulation',
            'description': 'Dive into JavaScript programming and learn how to create dynamic, interactive web pages by manipulating the Document Object Model (DOM).',
            'short_description': 'Add interactivity to your websites with JavaScript.',
            'duration': '3 weeks',
            'is_published': True
        },
        {
            'title': 'Backend Development with Node.js',
            'description': 'Explore server-side programming with Node.js. Learn to build scalable web applications and RESTful APIs.',
            'short_description': 'Build powerful backend systems with Node.js.',
            'duration': '4 weeks',
            'is_published': True
        },
        {
            'title': 'Full Stack Project',
            'description': 'Apply your skills in a comprehensive project. Build a full-stack web application from conception to deployment.',
            'short_description': 'Culminate your learning with a real-world project.',
            'duration': '3 weeks',
            'is_published': True
        }
    ],
    'Cloud Computing Essentials': [
        {
            'title': 'Introduction to Cloud Concepts',
            'description': 'Understand the fundamental concepts of cloud computing, including service models, deployment models, and key benefits.',
            'short_description': 'Get acquainted with core cloud computing principles.',
            'duration': '1 week',
            'is_published': True
        },
        {
            'title': 'AWS Fundamentals',
            'description': 'Explore Amazon Web Services (AWS) and learn to use key services like EC2, S3, and RDS.',
            'short_description': 'Dive into the AWS ecosystem and its core services.',
            'duration': '3 weeks',
            'is_published': True
        },
        {
            'title': 'Microsoft Azure Essentials',
            'description': 'Discover Microsoft Azure and its services. Learn to deploy and manage applications in the Azure cloud.',
            'short_description': 'Master the basics of Microsoft Azure.',
            'duration': '3 weeks',
            'is_published': True
        },
        {
            'title': 'Cloud Security and Compliance',
            'description': 'Learn about security best practices in the cloud, including identity management, data protection, and compliance frameworks.',
            'short_description': 'Ensure your cloud deployments are secure and compliant.',
            'duration': '1 week',
            'is_published': True
        }
    ],
    'Artificial Intelligence and Ethics': [
        {
            'title': 'Foundations of Artificial Intelligence',
            'description': 'Explore the history, concepts, and current state of AI. Learn about different AI approaches and their applications.',
            'short_description': 'Understand the core concepts and evolution of AI.',
            'duration': '2 weeks',
            'is_published': True
        },
        {
            'title': 'Machine Learning and Neural Networks',
            'description': 'Dive deep into machine learning algorithms and neural network architectures. Implement and train models for various tasks.',
            'short_description': 'Master the techniques behind modern AI systems.',
            'duration': '4 weeks',
            'is_published': True
        },
        {
            'title': 'AI Ethics and Societal Impact',
            'description': 'Examine the ethical implications of AI technologies. Discuss bias, fairness, transparency, and accountability in AI systems.',
            'short_description': 'Explore the ethical challenges posed by AI.',
            'duration': '2 weeks',
            'is_published': True
        },
        {
            'title': 'AI Policy and Governance',
            'description': 'Study current and proposed policies for AI governance. Analyze case studies and develop frameworks for responsible AI development.',
            'short_description': 'Understand the policy landscape surrounding AI.',
            'duration': '2 weeks',
            'is_published': True
        }
    ]
}

# Learning resources for each course
learning_resources_data = {
    'Introduction to Python for Data Science': [
        {
            'title': 'Python Basics Video Series',
            'description': 'A comprehensive video series covering Python basics for data science.',
            'resource_type': 'VIDEO',
            'order': 1
        },
        {
            'title': 'Python for Data Science Handbook',
            'description': 'An interactive e-book with hands-on examples and exercises.',
            'resource_type': 'DOCUMENT',
            'order': 2
        },
        {
            'title': 'NumPy and Pandas Tutorial',
            'description': 'In-depth tutorial on using NumPy and Pandas for data manipulation.',
            'resource_type': 'DOCUMENT',
            'order': 3
        },
        {
            'title': 'Python Data Types Quiz',
            'description': 'Test your understanding of Python data types and structures.',
            'resource_type': 'QUIZ',
            'order': 4
        }
    ],
    'Data Analysis and Visualization': [
        {
            'title': 'Exploratory Data Analysis Techniques',
            'description': 'Video lectures on various EDA techniques with real-world datasets.',
            'resource_type': 'VIDEO',
            'order': 1
        },
        {
            'title': 'Data Visualization Best Practices',
            'description': 'An interactive guide to creating effective and engaging data visualizations.',
            'resource_type': 'DOCUMENT',
            'order': 2
        },
        {
            'title': 'Matplotlib and Seaborn Masterclass',
            'description': 'Hands-on tutorial for creating advanced visualizations with Matplotlib and Seaborn.',
            'resource_type': 'VIDEO',
            'order': 3
        },
        {
            'title': 'Data Visualization Challenge',
            'description': 'Apply your skills to create insightful visualizations from a given dataset.',
            'resource_type': 'QUIZ',
            'order': 4
        }
    ],
    'Machine Learning Fundamentals': [
        {
            'title': 'Introduction to Machine Learning',
            'description': 'A comprehensive video course covering ML basics and algorithms.',
            'resource_type': 'VIDEO',
            'order': 1
        },
        {
            'title': 'Supervised Learning Algorithms',
            'description': 'Detailed explanations and implementations of key supervised learning algorithms.',
            'resource_type': 'DOCUMENT',
            'order': 2
        },
        {
            'title': 'Unsupervised Learning Techniques',
            'description': 'Explore clustering and dimensionality reduction techniques with practical examples.',
            'resource_type': 'DOCUMENT',
            'order': 3
        },
        {
            'title': 'Machine Learning Project: Predictive Modeling',
            'description': 'A guided project to build and evaluate a predictive model on a real-world dataset.',
            'resource_type': 'DOCUMENT',
            'order': 4
        },
        {
            'title': 'Machine Learning Algorithms Quiz',
            'description': 'Test your knowledge of various machine learning algorithms and their applications.',
            'resource_type': 'QUIZ',
            'order': 5
        }
    ],
    'Big Data Processing with PySpark': [
        {
            'title': 'Introduction to Distributed Computing',
            'description': 'Video series explaining the concepts of distributed computing and big data.',
            'resource_type': 'VIDEO',
            'order': 1
        },
        {
            'title': 'PySpark Fundamentals',
            'description': 'Interactive notebook with PySpark basics and data processing examples.',
            'resource_type': 'DOCUMENT',
            'order': 2
        },
        {
            'title': 'Advanced PySpark: Machine Learning with MLlib',
            'description': "Tutorial on using Spark's MLlib for scalable machine learning tasks.",
            'resource_type': 'DOCUMENT',
            'order': 3
        },
        {
            'title': 'Big Data Project: Log Analysis',
            'description': 'A comprehensive project to analyze large-scale log data using PySpark.',
            'resource_type': 'DOCUMENT',
            'order': 4
        },
        {
            'title': 'PySpark Concepts Quiz',
            'description': 'Test your understanding of PySpark concepts and best practices.',
            'resource_type': 'QUIZ',
            'order': 5
        }
    ],
    'HTML5 and CSS3 Fundamentals': [
        {
            'title': 'Web Design Principles',
            'description': 'An interactive guide to fundamental web design principles and best practices.',
            'resource_type': 'DOCUMENT',
            'order': 1
        },
        {
            'title': 'Responsive Design with CSS Grid and Flexbox',
            'description': 'Video tutorial series on creating responsive layouts using modern CSS techniques.',
            'resource_type': 'VIDEO',
            'order': 2
        },
        {
            'title': 'CSS Animation Workshop',
            'description': 'Hands-on workshop for creating engaging animations with CSS.',
            'resource_type': 'DOCUMENT',
            'order': 3
        },
        {
            'title': 'HTML5 and CSS3 Coding Challenge',
            'description': 'Apply your HTML and CSS skills to create a responsive web page.',
            'resource_type': 'QUIZ',
            'order': 4
        }
    ],
    'JavaScript and DOM Manipulation': [
        {
            'title': 'JavaScript Fundamentals Quiz',
            'description': 'Interactive quiz to test and reinforce your JavaScript knowledge.',
            'resource_type': 'QUIZ',
            'order': 1
        },
        {
            'title': 'Building Interactive Web Components',
            'description': 'Step-by-step guide to creating reusable web components with JavaScript.',
            'resource_type': 'DOCUMENT',
            'order': 2
        },
        {
            'title': 'Advanced DOM Manipulation Techniques',
            'description': 'Video series covering advanced topics in DOM manipulation and event handling.',
            'resource_type': 'VIDEO',
            'order': 3
        },
        {
            'title': 'JavaScript Debugging Techniques',
            'description': 'Learn effective strategies for debugging JavaScript code.',
            'resource_type': 'VIDEO',
            'order': 4
        }
    ],
    'Backend Development with Node.js': [
        {
            'title': 'Introduction to Node.js',
            'description': 'Video series introducing Node.js and its core concepts.',
            'resource_type': 'VIDEO',
            'order': 1
        },
        {
            'title': 'Building RESTful APIs with Express',
            'description': 'Step-by-step guide to creating robust RESTful APIs using Express.js.',
            'resource_type': 'DOCUMENT',
            'order': 2
        },
        {
            'title': 'Database Integration with MongoDB',
            'description': 'Learn how to integrate MongoDB with your Node.js applications.',
            'resource_type': 'VIDEO',
            'order': 3
        },
        {
            'title': 'Node.js Security Best Practices',
            'description': 'Comprehensive guide to securing your Node.js applications.',
            'resource_type': 'DOCUMENT',
            'order': 4
        },
        {
            'title': 'Node.js Concepts Quiz',
            'description': 'Test your understanding of Node.js and backend development concepts.',
            'resource_type': 'QUIZ',
            'order': 5
        }
    ],
    'Full Stack Project': [
        {
            'title': 'Project Planning and Architecture',
            'description': 'Learn how to plan and architect a full-stack web application.',
            'resource_type': 'DOCUMENT',
            'order': 1
        },
        {
            'title': 'Frontend Development with React',
            'description': 'Video series on building the frontend of your project using React.',
            'resource_type': 'VIDEO',
            'order': 2
        },
        {
            'title': 'Backend API Development',
            'description': 'Guide to developing a robust backend API for your full-stack project.',
            'resource_type': 'DOCUMENT',
            'order': 3
        },
        {
            'title': 'Database Design and Implementation',
            'description': 'Learn how to design and implement a database for your full-stack application.',
            'resource_type': 'VIDEO',
            'order': 4
        },
        {
            'title': 'Full Stack Project Quiz',
            'description': 'Test your understanding of full-stack development concepts.',
            'resource_type': 'QUIZ',
            'order': 5
        }
    ],
    'Introduction to Cloud Concepts': [
        {
            'title': 'Cloud Computing Fundamentals',
            'description': 'Video introduction to basic cloud computing concepts and models.',
            'resource_type': 'VIDEO',
            'order': 1
        },
        {
            'title': 'Cloud Service Models Explained',
            'description': 'Detailed guide on IaaS, PaaS, and SaaS with real-world examples.',
            'resource_type': 'DOCUMENT',
            'order': 2
        },
        {
            'title': 'Cloud Deployment Models',
            'description': 'Learn about public, private, and hybrid cloud deployment models.',
            'resource_type': 'VIDEO',
            'order': 3
        },
        {
            'title': 'Cloud Computing Concepts Quiz',
            'description': 'Test your understanding of core cloud computing concepts.',
            'resource_type': 'QUIZ',
            'order': 4
        }
    ],
    'AWS Fundamentals': [
        {
            'title': 'AWS Services Overview',
            'description': 'Comprehensive guide to core AWS services and their use cases.',
            'resource_type': 'DOCUMENT',
            'order': 1
        },
        {
            'title': 'Launching EC2 Instances Lab',
            'description': 'Hands-on lab for launching and configuring EC2 instances in AWS.',
            'resource_type': 'DOCUMENT',
            'order': 2
        },
        {
            'title': 'AWS Security Best Practices',
            'description': 'Video lecture on implementing security best practices in AWS environments.',
            'resource_type': 'VIDEO',
            'order': 3
        },
        {
            'title': 'AWS Storage Solutions',
            'description': 'Learn about different AWS storage options like S3, EBS, and EFS.',
            'resource_type': 'VIDEO',
            'order': 4
        },
        {
            'title': 'AWS Services Quiz',
            'description': 'Test your knowledge of various AWS services and their applications.',
            'resource_type': 'QUIZ',
            'order': 5
        }
    ],
    'Microsoft Azure Essentials': [
        {
            'title': 'Introduction to Azure Services',
            'description': 'Overview of core Azure services and their capabilities.',
            'resource_type': 'VIDEO',
            'order': 1
        },
        {
            'title': 'Azure Virtual Machines Deployment',
            'description': 'Step-by-step guide to deploying and managing Azure VMs.',
            'resource_type': 'DOCUMENT',
            'order': 2
        },
        {
            'title': 'Azure Networking Fundamentals',
            'description': 'Learn about Azure networking concepts and best practices.',
            'resource_type': 'VIDEO',
            'order': 3
        },
        {
            'title': 'Azure Storage Solutions',
            'description': 'Explore various storage options available in Azure.',
            'resource_type': 'DOCUMENT',
            'order': 4
        },
        {
            'title': 'Azure Concepts Quiz',
            'description': 'Test your understanding of Microsoft Azure services and concepts.',
            'resource_type': 'QUIZ',
            'order': 5
        }
    ],
    'Cloud Security and Compliance': [
        {
            'title': 'Cloud Security Fundamentals',
            'description': 'Video series introducing core cloud security concepts and challenges.',
            'resource_type': 'VIDEO',
            'order': 1
        },
        {
            'title': 'Identity and Access Management in the Cloud',
            'description': 'Comprehensive guide to implementing IAM in cloud environments.',
            'resource_type': 'DOCUMENT',
            'order': 2
        },
        {
            'title': 'Data Protection and Encryption',
            'description': 'Learn about data protection strategies and encryption in the cloud.',
            'resource_type': 'VIDEO',
            'order': 3
        },
        {
            'title': 'Compliance Frameworks for Cloud Computing',
            'description': 'Overview of major compliance frameworks relevant to cloud computing.',
            'resource_type': 'DOCUMENT',
            'order': 4
        },
        {
            'title': 'Cloud Security Quiz',
            'description': 'Test your knowledge of cloud security principles and best practices.',
            'resource_type': 'QUIZ',
            'order': 5
        }
    ],
    'Foundations of Artificial Intelligence': [
        {
            'title': 'AI History and Evolution',
            'description': 'Video lecture on the history and evolution of artificial intelligence.',
            'resource_type': 'VIDEO',
            'order': 1
        },
        {
            'title': 'AI Approaches and Paradigms',
            'description': 'Comprehensive guide to different AI approaches and paradigms.',
            'resource_type': 'DOCUMENT',
            'order': 2
        },
        {
            'title': 'Applications of AI in Various Industries',
            'description': 'Explore real-world applications of AI across different sectors.',
            'resource_type': 'VIDEO',
            'order': 3
        },
        {
            'title': 'Future Trends in AI',
            'description': 'Discussion on emerging trends and future directions in AI research.',
            'resource_type': 'DOCUMENT',
            'order': 4
        },
        {
            'title': 'AI Foundations Quiz',
            'description': 'Test your understanding of AI fundamentals and concepts.',
            'resource_type': 'QUIZ',
            'order': 5
        }
    ],
    'Machine Learning and Neural Networks': [
        {
            'title': 'Introduction to TensorFlow',
            'description': 'Tutorial on getting started with TensorFlow for machine learning projects.',
            'resource_type': 'DOCUMENT',
            'order': 1
        },
        {
            'title': 'Convolutional Neural Networks Explained',
            'description': 'In-depth video series on the architecture and applications of CNNs.',
            'resource_type': 'VIDEO',
            'order': 2
        },
        {
            'title': 'Natural Language Processing with BERT',
            'description': 'Practical guide to implementing BERT for NLP tasks.',
            'resource_type': 'DOCUMENT',
            'order': 3
        },
        {
            'title': 'Reinforcement Learning Fundamentals',
            'description': 'Video tutorial on the basics of reinforcement learning.',
            'resource_type': 'VIDEO',
            'order': 4
        },
        {
            'title': 'Neural Networks and Deep Learning Quiz',
            'description': 'Test your knowledge of neural network architectures and deep learning concepts.',
            'resource_type': 'QUIZ',
            'order': 5
        }
    ],
    'AI Ethics and Societal Impact': [
        {
            'title': 'Introduction to AI Ethics',
            'description': 'Video lecture introducing key ethical considerations in AI development and deployment.',
            'resource_type': 'VIDEO',
            'order': 1
        },
        {
            'title': 'Bias and Fairness in AI Systems',
            'description': 'Comprehensive guide on identifying and mitigating bias in AI systems.',
            'resource_type': 'DOCUMENT',
            'order': 2
        },
        {
            'title': 'AI Transparency and Explainability',
            'description': 'Learn about the importance of transparency and explainability in AI systems.',
            'resource_type': 'VIDEO',
            'order': 3
        },
        {
            'title': 'Case Studies in AI Ethics',
            'description': 'Analysis of real-world ethical dilemmas in AI applications.',
            'resource_type': 'DOCUMENT',
            'order': 4
        },
        {
            'title': 'AI Ethics Quiz',
            'description': 'Test your understanding of ethical principles in AI development and deployment.',
            'resource_type': 'QUIZ',
            'order': 5
        }
    ],
    'AI Policy and Governance': [
        {
            'title': 'AI Policy Landscape',
            'description': 'Overview of current AI policies and regulations across different countries.',
            'resource_type': 'VIDEO',
            'order': 1
        },
        {
            'title': 'Governance Frameworks for AI',
            'description': 'Detailed guide on various governance frameworks for responsible AI development.',
            'resource_type': 'DOCUMENT',
            'order': 2
        },
        {
            'title': 'AI Risk Assessment and Management',
            'description': 'Learn how to assess and manage risks associated with AI systems.',
            'resource_type': 'VIDEO',
            'order': 3
        },
        {
            'title': 'Future of AI Regulation',
            'description': 'Discussion on emerging trends and future directions in AI regulation.',
            'resource_type': 'DOCUMENT',
            'order': 4
        },
        {
            'title': 'AI Policy and Governance Quiz',
            'description': 'Test your knowledge of AI policy, governance, and regulatory concepts.',
            'resource_type': 'QUIZ',
            'order': 5
        }
    ]
}

class Command(BaseCommand):
    help = 'Populates the database with sample program data'

    def handle(self, *args, **kwargs):
        # Use an existing user or create a new one
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.create_superuser('admin', 'admin@example.com', 'adminpassword')

        # Create programs
        for program_data in programs_data:
            program = Program.objects.create(
                title=program_data['title'],
                description=program_data['description'],
                short_description=program_data['short_description'],
                program_type=program_data['program_type'],
                duration=program_data['duration'],
                level=program_data['level'],
                is_published=program_data['is_published'],
                created_by=user
            )

            # Create courses for each program
            if program.title in courses_data:
                for course_data in courses_data[program.title]:
                    course = Course.objects.create(
                        program=program,
                        title=course_data['title'],
                        description=course_data['description'],
                        short_description=course_data['short_description'],
                        duration=course_data['duration'],
                        is_published=course_data['is_published'],
                        created_by=user
                    )

                    # Create learning resources for each course
                    if course.title in learning_resources_data:
                        for resource_data in learning_resources_data[course.title]:
                            LearningResource.objects.create(
                                course=course,
                                title=resource_data['title'],
                                description=resource_data['description'],
                                resource_type=resource_data['resource_type'],
                                order=resource_data['order']
                            )

        self.stdout.write(self.style.SUCCESS('Successfully populated the database with sample program data'))