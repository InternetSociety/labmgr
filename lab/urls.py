from django.urls import path

import lab.views.dashboard
import lab.views.exercise
import lab.views.utils
import lab.views.welcome

urlpatterns = [
    path('<int:project_id>/dashboard/', lab.views.dashboard.Dashboard.as_view(), name='project_dashboard'),
    path('<int:project_id>/drawing/', lab.views.utils.DrawingView.as_view(), name='project_drawing'),
    path('<int:project_id>/start/', lab.views.exercise.StartExerciseView.as_view(), name='project_start'),
    path('<int:project_id>/stop/', lab.views.exercise.StopExerciseView.as_view(), name='project_stop'),
    path('<int:project_id>/clone/', lab.views.welcome.CloneTemplateView.as_view(), name='template_clone'),
    path('node/<int:node_id>/reload/', lab.views.exercise.ReloadNodeView.as_view(), name='node_reboot'),
    path('symbols/<path:symbol_id>', lab.views.utils.SymbolView.as_view(), name='symbol'),
]
