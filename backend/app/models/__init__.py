"""
Importing every model module here (and importing this package from
alembic/env.py) ensures all tables register on Base.metadata before
autogenerate runs — a model that isn't imported anywhere is invisible to
Alembic, a common and easy-to-miss mistake (see docs/DATABASE.md).
"""
from app.models.assistant_conversation import AssistantConversation, AssistantMessage  # noqa: F401
from app.models.assistant_feedback import AssistantFeedback, AssistantPreference  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.advisory_feedback import AdvisoryFeedback  # noqa: F401
from app.models.ai_analysis import AIAnalysis  # noqa: F401
from app.models.ai_analysis_session import AIAnalysisSession  # noqa: F401
from app.models.ai_crop_stage_result import AICropStageResult  # noqa: F401
from app.models.ai_model_registry import AIModelRegistry  # noqa: F401
from app.models.buyer_business_profile import BuyerBusinessProfile  # noqa: F401
from app.models.buyer_offer import BuyerOffer, CounterOffer  # noqa: F401
from app.models.case_assignment import CaseAssignment  # noqa: F401
from app.models.case_consent import CaseConsent  # noqa: F401
from app.models.case_review import CaseReview  # noqa: F401
from app.models.consent_record import ConsentRecord  # noqa: F401
from app.models.crop_cycle import CropCycle  # noqa: F401
from app.models.crop_cycle_stage_history import CropCycleStageHistory  # noqa: F401
from app.models.crop_health_case import CropHealthCase  # noqa: F401
from app.models.crop_master import CropMaster  # noqa: F401
from app.models.crop_photo import CropPhoto  # noqa: F401
from app.models.crop_photo_session import CropPhotoSession  # noqa: F401
from app.models.crop_variety import CropVariety  # noqa: F401
from app.models.crop_stage_definition import CropStageDefinition  # noqa: F401
from app.models.dealer_business_profile import DealerBusinessProfile  # noqa: F401
from app.models.dealer_price_history import DealerPriceHistory  # noqa: F401
from app.models.dealer_product import DealerProduct  # noqa: F401
from app.models.delivery import Delivery  # noqa: F401
from app.models.disease_class import DiseaseClass  # noqa: F401
from app.models.farm import Farm  # noqa: F401
from app.models.farmer_profile import FarmerProfile  # noqa: F401
from app.models.harvest_listing import HarvestListing  # noqa: F401
from app.models.crop_cost_estimate import CropCostEstimate  # noqa: F401
from app.models.harvest_record import HarvestRecord  # noqa: F401
from app.models.invoice import Invoice  # noqa: F401
from app.models.ledger_entry import LedgerEntry  # noqa: F401
from app.models.knowledge_entry import AIEvaluationRecord, KnowledgeEntry  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.notification_preference import NotificationPreference  # noqa: F401
from app.models.order import Order, OrderItem  # noqa: F401
from app.models.order_dispute import OrderDispute, Refund  # noqa: F401
from app.models.payment import Payment  # noqa: F401
from app.models.photo_access_grant import PhotoAccessGrant  # noqa: F401
from app.models.plot import Plot  # noqa: F401
from app.models.price_anomaly_flag import PriceAnomalyFlag  # noqa: F401
from app.models.product import Product  # noqa: F401
from app.models.professional_feedback import ProfessionalFeedback  # noqa: F401
from app.models.professional_profile import ProfessionalProfile  # noqa: F401
from app.models.reference_price import ReferencePrice  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.role import Role, UserRole  # noqa: F401
from app.models.sale_dispute import DemandSignal, QualityDispute, SaleDispute, SaleFeedback  # noqa: F401
from app.models.sale_order import SaleOrder  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.treatment_follow_up import TreatmentFollowUp  # noqa: F401
from app.models.treatment_record import TreatmentRecord  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.verification_record import VerificationRecord  # noqa: F401
from app.models.weather_snapshot import WeatherSnapshot  # noqa: F401
