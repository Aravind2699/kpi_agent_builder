from django.urls import path

from . import views

urlpatterns = [
    path("generate-questions/", views.generate_questions, name="generate_questions"),
    path("build-intent/", views.build_intent, name="build_intent"),
    path("validate-intent/", views.validate_intent, name="validate_intent"),
    path("calculate-kpi/", views.calculate_kpi, name="calculate_kpi"),
    path("reset-session/", views.reset_session, name="reset_session"),
    path("schema/", views.schema, name="schema"),
]
