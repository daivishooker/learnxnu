.class final Lcom/hardening/shell/HardeningApp$GuardReport;
.super Ljava/lang/Object;
.source "HardeningApp.java"


# annotations
.annotation system Ldalvik/annotation/EnclosingClass;
    value = Lcom/hardening/shell/HardeningApp;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x18
    name = "GuardReport"
.end annotation


# instance fields
.field final ok:Z

.field final reasons:Ljava/lang/String;


# direct methods
.method constructor <init>(ZLjava/lang/String;)V
    .locals 0

    .line 144
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 145
    iput-boolean p1, p0, Lcom/hardening/shell/HardeningApp$GuardReport;->ok:Z

    .line 146
    iput-object p2, p0, Lcom/hardening/shell/HardeningApp$GuardReport;->reasons:Ljava/lang/String;

    .line 147
    return-void
.end method
