import logging
import typing

from starlette import status as http_status_codes
from fastapi import APIRouter, UploadFile, File, Depends, Body

from robot_server.service.dependencies import get_protocol_manager
from robot_server.service.json_api import ResourceLink
from robot_server.service.json_api.resource_links import ResourceLinkKey, ResourceLinks
from robot_server.service.protocol import models as route_models
from robot_server.service.protocol.manager import ProtocolManager
from robot_server.service.protocol.protocol import UploadedProtocol

log = logging.getLogger(__name__)

router = APIRouter()

PATH_ROOT = "/protocols"
PATH_PROTOCOL_ID = PATH_ROOT + "/{protocolId}"


@router.post(
    PATH_ROOT,
    description="Create a protocol",
    response_model_exclude_unset=True,
    response_model=route_models.ProtocolResponse,
    status_code=http_status_codes.HTTP_201_CREATED,
)
async def create_protocol(
    protocolFile: UploadFile = File(..., description="The protocol file"),
    supportFiles: typing.List[UploadFile] = Body(
        default=list(),
        description="Any support files needed by the protocol (ie data "
        "files, additional python files)",
    ),
    protocol_manager=Depends(get_protocol_manager),
):
    """Create protocol from proto file plus optional support files"""
    new_proto = protocol_manager.create(
        protocol_file=protocolFile,
        support_files=supportFiles,
    )
    return route_models.ProtocolResponse(
        data=_to_response(new_proto),
        links=get_protocol_links(router, new_proto.data.identifier),
    )


@router.get(
    PATH_ROOT,
    description="Get all protocols",
    response_model_exclude_unset=True,
    response_model=route_models.MultiProtocolResponse,
)
async def get_protocols(
    protocol_manager: ProtocolManager = Depends(get_protocol_manager),
):
    return route_models.MultiProtocolResponse(
        data=[_to_response(u) for u in protocol_manager.get_all()],
        links=get_root_links(router),
    )


@router.get(
    PATH_PROTOCOL_ID,
    description="Get a protocol",
    response_model_exclude_unset=True,
    response_model=route_models.ProtocolResponse,
)
async def get_protocol(
    protocolId: str, protocol_manager: ProtocolManager = Depends(get_protocol_manager)
):
    proto = protocol_manager.get(protocolId)
    return route_models.ProtocolResponse(
        data=_to_response(proto),
        links=get_protocol_links(router, proto.data.identifier),
    )


@router.delete(
    PATH_PROTOCOL_ID,
    description="Delete a protocol",
    response_model_exclude_unset=True,
    response_model=route_models.ProtocolResponse,
)
async def delete_protocol(
    protocolId: str, protocol_manager: ProtocolManager = Depends(get_protocol_manager)
):
    proto = protocol_manager.remove(protocolId)
    return route_models.ProtocolResponse(
        data=_to_response(proto),
        links=get_root_links(router),
    )


@router.patch(
    PATH_PROTOCOL_ID,
    description="Add a new file or replace an existing file in the protocol.",
    response_model_exclude_unset=True,
    response_model=route_models.ProtocolResponse,
    status_code=http_status_codes.HTTP_200_OK,
)
async def upload_file(
    protocolId: str,
    file: UploadFile = File(...),
    protocol_manager: ProtocolManager = Depends(get_protocol_manager),
):
    proto = protocol_manager.get(protocolId)
    proto.update(file)
    return route_models.ProtocolResponse(
        data=_to_response(proto),
        links=get_protocol_links(router, proto.data.identifier),
    )


def _to_response(
    uploaded_protocol: UploadedProtocol,
) -> route_models.ProtocolResponseAttributes:
    """Create ProtocolResponse from an UploadedProtocol"""
    meta = uploaded_protocol.data
    analysis_result = uploaded_protocol.data.analysis_result
    return route_models.ProtocolResponseAttributes(
        id=meta.identifier,
        protocolFile=route_models.FileAttributes(
            basename=meta.contents.protocol_file.path.name
        ),
        supportFiles=[
            route_models.FileAttributes(basename=s.path.name)
            for s in meta.contents.support_files
        ],
        lastModifiedAt=meta.last_modified_at,
        createdAt=meta.created_at,
        metadata=analysis_result.meta,
        requiredEquipment=analysis_result.required_equipment,
        errors=analysis_result.errors,
    )


ROOT_RESOURCE = ResourceLink(href=router.url_path_for(get_protocols.__name__))
PROTOCOL_BY_ID_RESOURCE = ResourceLink(href=PATH_PROTOCOL_ID)


def get_root_links(api_router: APIRouter) -> ResourceLinks:
    """Get resource links for root path handlers"""
    return {
        ResourceLinkKey.self: ROOT_RESOURCE,
        ResourceLinkKey.protocol_by_id: PROTOCOL_BY_ID_RESOURCE,
    }


def get_protocol_links(api_router: APIRouter, protocol_id: str) -> ResourceLinks:
    """Get resource links for specific resource path handlers"""
    return {
        ResourceLinkKey.self: ResourceLink(
            href=api_router.url_path_for(get_protocol.__name__, protocolId=protocol_id)
        ),
        ResourceLinkKey.protocols: ROOT_RESOURCE,
        ResourceLinkKey.protocol_by_id: PROTOCOL_BY_ID_RESOURCE,
    }
