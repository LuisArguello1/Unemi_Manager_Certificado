from django.urls import reverse

class MenuService:
    """
    Servicio para generar la estructura del menú lateral (Sidebar).
    Centraliza la definición de items y el cálculo de estado activo.
    """
    
    @staticmethod
    def get_menu_items(current_path, user):
        """
        Retorna la lista de items del menú filtrada por permisos.
        """
        
        try:
            dashboard_url = reverse('core:dashboard')
        except:
            dashboard_url = '#'

        menu = []
        
        # =====================================================================
        # DASHBOARD
        # =====================================================================
        menu.append({
            'name': 'Dashboard',
            'icon': 'chart-line',
            'url': dashboard_url,
            'active': current_path == dashboard_url
        })
        
        # =====================================================================
        # CERTIFICADOS
        # =====================================================================
        menu.append({'separator': True, 'label': 'CERTIFICADOS'})
        
        try:
            certificado_crear_url = reverse('certificado:crear')
            certificado_lista_url = reverse('certificado:lista')
            certificado_plantilla_url = reverse('certificado:plantilla_list')
            certificado_direccion_url = reverse('certificado:direccion_list')
            modalidad_url = reverse('certificado:modalidad_list')
            tipo_url = reverse('certificado:tipo_list')
            tipo_evento_url = reverse('certificado:tipo_evento_list')
        except:
            certificado_crear_url = '#'
            certificado_lista_url = '#'
            certificado_plantilla_url = '#'
            certificado_direccion_url = '#'
            modalidad_url = '#'
            tipo_url = '#'
            tipo_evento_url = '#'
        
        menu.append({
            'name': 'Generar Certificados',
            'icon': 'file-signature',
            'url': certificado_crear_url,
            'active': current_path == certificado_crear_url
        })
        
        menu.append({
            'name': 'Historial',
            'icon': 'list-check',
            'url': certificado_lista_url,
            'active': (current_path == certificado_lista_url or 
                      (current_path.startswith('/certificados/lista')))
        })
        
        menu.append({
            'name': 'Plantillas',
            'icon': 'file-word',
            'url': certificado_plantilla_url,
            'active': 'plantillas' in current_path
        })
        
        menu.append({
            'name': 'Direcciones',
            'icon': 'building',
            'url': certificado_direccion_url,
            'active': 'direcciones' in current_path
        })

        menu.append({
            'name': 'Modalidades',
            'icon': 'tag',
            'url': modalidad_url,
            'active': 'modalidades' in current_path
        })

        menu.append({
            'name': 'Tipos Generales',
            'icon': 'tags',
            'url': tipo_url,
            'active': 'tipos/' in current_path and 'evento' not in current_path
        })

        menu.append({
            'name': 'Tipos de Evento',
            'icon': 'calendar-check',
            'url': tipo_evento_url,
            'active': 'tipos-evento' in current_path
        })
        
        # =====================================================================
        # CURSOS
        # =====================================================================
        menu.append({'separator': True, 'label': 'GESTIÓN DE CURSOS'})

        try:
            curso_list_url = reverse('curso:list')
            curso_create_url = reverse('curso:create')
            curso_plantilla_list_url = reverse('curso:plantilla_list')
        except:
            curso_list_url = '#'
            curso_create_url = '#'
            curso_plantilla_list_url = '#'

        menu.append({
            'name': 'Listado de Cursos',
            'icon': 'book-open',
            'url': curso_list_url,
            'active': (current_path.startswith('/curso/') and 
                      'plantillas' not in current_path and 
                      current_path != curso_create_url)
        })

        menu.append({
            'name': 'Nuevo Curso',
            'icon': 'plus-square',
            'url': curso_create_url,
            'active': current_path == curso_create_url
        })

        menu.append({
            'name': 'Plantillas Cursos',
            'icon': 'file-alt',
            'url': curso_plantilla_list_url,
            'active': current_path.startswith('/curso/') and 'plantillas' in current_path
        })
        
        # =====================================================================
        # CORREOS MASIVOS
        # =====================================================================
        menu.append({'separator': True, 'label': 'CORREO MASIVO'})
        
        try:
            correo_list_url = reverse('correo:list')
            correo_create_url = reverse('correo:create')
        except:
            correo_list_url = '#'
            correo_create_url = '#'
        
        menu.append({
            'name': 'Nueva Campaña',
            'icon': 'paper-plane',
            'url': correo_create_url,
            'active': current_path == correo_create_url
        })
        
        menu.append({
            'name': 'Historial Campañas',
            'icon': 'envelope-open-text',
            'url': correo_list_url,
            'active': (current_path == correo_list_url or 
                      (current_path.startswith('/correo/') and current_path != correo_create_url))
        })
        
        # =====================================================================
        # ADMINISTRACIÓN (Solo Staff/Superuser)
        # =====================================================================
        if user and (user.is_staff or user.is_superuser):
            menu.append({'separator': True, 'label': 'ADMINISTRACIÓN'})
            
            try:
                users_url = reverse('accounts:user_list')
            except:
                users_url = '#'
            
            menu.append({
                'name': 'Usuarios',
                'icon': 'users',
                'url': users_url,
                'active': current_path == users_url
            })

        return menu
