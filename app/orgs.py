from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Organization, OrgMember
from app.deps import get_current_user

router = APIRouter(prefix="/orgs", tags=["Organizations"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/create")
def create_org(
    name: str,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    org = Organization(name=name, owner_id=user_id, wallet=0)
    db.add(org)
    db.commit()
    db.add(OrgMember(org_id=org.id, user_id=user_id, role="owner"))
    db.commit()
    return {"org_id": org.id}

@router.post("/invite")
def invite_member(
    org_id: int,
    member_user_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    owner = db.query(Organization).filter(
        Organization.id == org_id,
        Organization.owner_id == user_id
    ).first()
    if not owner:
        raise HTTPException(status_code=403)

    db.add(OrgMember(org_id=org_id, user_id=member_user_id, role="member"))
    db.commit()
    return {"status": "member added"}
