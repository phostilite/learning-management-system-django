from organization.models import Organization 

def organization_logo(request):
    try:
        organization = Organization.objects.first()  
        return {'organization': organization}
    except Organization.DoesNotExist:
        return {'organization': None}