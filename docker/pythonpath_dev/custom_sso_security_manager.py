from superset.security import SupersetSecurityManager
import logging

logger = logging.getLogger(__name__)


class CustomSsoSecurityManager(SupersetSecurityManager):

    def request_loader(self, request):
        username = request.headers.get("X-User-Login")

        if not username:
            return None

        # Tenta achar o usuário pelo username ou email
        user = self.find_user(username=username)
        if not user:
            user = self.find_user(email=username)

        if not user and self.auth_user_registration:
            role = self.find_role(self.auth_user_registration_role)
            if not role:
                logger.error(f"Role '{self.auth_user_registration_role}' não encontrada!")
                return None

            # Monta nome/email a partir do username
            if "@" in username:
                first_name = username.split("@")[0]
                email = username
            else:
                first_name = username
                email = f"{username}@sso.local"

            try:
                user = self.add_user(
                    username=username,
                    first_name=first_name,
                    last_name="SSO",
                    email=email,
                    role=[role],  # <-- lista
                )
                logger.info(f"✅ Usuário SSO criado: {username}")
            except Exception as e:
                logger.error(f"❌ Erro ao criar usuário {username}: {e}")
                return None

        if user:
            # Garante que o usuário tem roles — corrige usuários criados sem role
            if not user.roles:
                role = self.find_role(self.auth_user_registration_role)
                if role:
                    user.roles = [role]
                    self.update_user(user)
                    logger.info(f"✅ Role '{self.auth_user_registration_role}' atribuída ao usuário existente: {username}")
            
            logger.info(f"✅ Login SSO: {username}")
            return user

        return None