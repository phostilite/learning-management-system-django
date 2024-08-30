from django.shortcuts import render, redirect
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont
import io
import os
from django.conf import settings
from .models import Certificate
import uuid

def generate_certificate(request):
    if request.method == 'POST':
        user_name = request.POST['user_name']
        course_name = request.POST['course_name']

        # Open the template image
        template_path = os.path.join(settings.BASE_DIR, 'certificate.png')
        with Image.open(template_path) as template:
            # Create a drawing object
            draw = ImageDraw.Draw(template)

            # Load fonts
            user_name_font_path = os.path.join(settings.BASE_DIR, 'Roboto-Medium.ttf')
            user_name_font = ImageFont.truetype(user_name_font_path, 120)

            course_name_font_path = os.path.join(settings.BASE_DIR, 'Roboto-Regular.ttf')
            course_name_font = ImageFont.truetype(course_name_font_path, 80)

            # Center and draw user name
            user_name_point_a = (540, 720)  # Left boundary for user name
            user_name_point_b = (1480, 770)  # Right boundary for user name
            user_name_position = center_text(draw, user_name, user_name_font, user_name_point_a, user_name_point_b)
            draw.text(user_name_position, user_name, font=user_name_font, fill=(0, 0, 0))

            # Center and draw course name
            course_name_point_a = (540, 1000)  # Left boundary for course name
            course_name_point_b = (1480, 1000)  # Right boundary for course name
            course_name_position = center_text(draw, course_name, course_name_font, course_name_point_a, course_name_point_b)
            draw.text(course_name_position, course_name, font=course_name_font, fill=(0, 0, 0))

            # Save the image to a bytes buffer
            buffer = io.BytesIO()
            template.save(buffer, format='PNG')
            image_content = ContentFile(buffer.getvalue())

            # Generate a unique certificate number
            certificate_number = str(uuid.uuid4())[:8].upper()

            # Create and save the certificate
            certificate = Certificate(
                user_name=user_name,
                course_name=course_name,
                certificate_number=certificate_number
            )
            certificate.certificate_image.save(f"{certificate_number}_{user_name}_certificate.png", image_content)
            certificate.save()

        return redirect('certificate_display', id=certificate.id)
    else:
        return render(request, 'certificates/certificate_form.html')

def center_text(draw, text, font, point_a, point_b):
    text_width = draw.textlength(text, font=font)
    available_width = point_b[0] - point_a[0]
    start_x = point_a[0] + (available_width - text_width) / 2
    return (start_x, point_a[1])

def draw_mark(draw, point, size=10, color=(255, 0, 0)):
    x, y = point
    draw.ellipse((x - size, y - size, x + size, y + size), outline=color, width=2)

def certificate_display(request, id):
    certificate = Certificate.objects.get(id=id)
    return render(request, 'certificates/certificate_display.html', {'certificate': certificate})