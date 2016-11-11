## Script (Python) "resolveuid"
##title=Retrieve an object using its UID
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=uuid='',redirect=True
# (reference_url is supposed to do the same thing, but is broken)
from Products.CMFCore.utils import getToolByName
from Products.PythonScripts.standard import html_quote
from AccessControl import Unauthorized

request = context.REQUEST
response = request.RESPONSE

if not uuid:
    try:
        uuid = traverse_subpath.pop(0)
    except:
        raise Unauthorized, context

reference_tool = getToolByName(context, 'reference_catalog')
obj = reference_tool.lookupObject(uuid)


def redirectBasedOnVersionUID(context, uuid, redirect):
    """ Version UID based redirect
    """
    portal = context.restrictedTraverse('plone_portal_state').portal()
    permalink_folder = portal.get('eea_permalink_objects')
    if permalink_folder:
        value = permalink_folder.get(uuid)
        if value:
            uuid = value.versionId
        else:
            data_dict = context.restrictedTraverse('dataVersions')()
            value = data_dict.get(uuid)
            if value:
                uuid = value
    query = {'getVersionId': uuid,
             'show_inactive': True,
             'sort_on': 'effective'}
    resView = context.restrictedTraverse('@@getDataForRedirect')
    res = resView(query)
    if len(res) > 0:
        target_obj = res[-1]
        target = target_obj.getURL()
        if not redirect:
            # return find url
            return target
        return response.redirect(target, lock=1)

def redirectBasedOnShortId(context, redirect):
    """ Short ID based redirect
    """
    if context.getId() == 'figures':
        ptype = 'EEAFigure'
    elif context.getId() == 'data':
        ptype = 'Data'
    else:
        ptype = None

    if ptype:
        query = {'portal_type': ptype,
                 'show_inactive': True,
                 'getShortId': request.get('id', None)}
        resView = context.restrictedTraverse('@@getDataForRedirect')
        res = resView(query)
        if len(res) > 0:
            target = context.absolute_url() + '/' + res[0].getId
            if not redirect:
                return target
            return response.redirect(target, lock=1)

def redirectNotFound(redirect):
    """ Redirect not found
    """
    if not redirect:
        return None

    return response.notFoundError(
        'The link you followed appears to be broken!')

def redirectBasedOnObjectUID(obj, redirect):
    """ Object UID based redirect
    """
    if traverse_subpath:
        traverse_subpath.insert(0, obj.absolute_url())
        target = '/'.join(traverse_subpath)
    else:
        target = obj.absolute_url()
    
    if request.QUERY_STRING:
        target += '?' + request.QUERY_STRING
    
    if not redirect:
        return target
    
    return response.redirect(target, status=301)

if not obj:
    hook = getattr(context, 'kupu_resolveuid_hook', None)
    if hook:
        obj = hook(uuid)

    if not obj:
        redirectBasedOnVersionUID(context, uuid, redirect)
        redirectBasedOnShortId(context, redirect)
        redirectNotFound(redirect)
else:
    redirectBasedOnObjectUID(obj, redirect)
