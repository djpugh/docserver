import logging

logger = logging.getLogger(__name__)


def get_permissions(user):
    logger.debug(user)
    user_domain = user.email.split('@')[1]
    # The user can access the permissions for their domain e.g joe.blogs@mycompany.com can access all the com.mycompany/read documentation
    user_domain_read_permission = '.'.join(user_domain.split('.')[::-1])+'/read'
    return ['com/read', user_domain_read_permission]
