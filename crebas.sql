/*==============================================================*/
/* DBMS name:      MySQL 5.0                                    */
/* Created on:     28.05.2023 18:07:02                          */
/*==============================================================*/

/*==============================================================*/
/* Table: CLOSED_TICKETS                                        */
/*==============================================================*/
create table if not exists CLOSED_TICKETS
(
   REASON               varchar(100) not null,
   TICKET_ID            int not null auto_increment,
   primary key (TICKET_ID)
);

/*==============================================================*/
/* Table: DEVELOPERS                                            */
/*==============================================================*/
create table if not exists DEVELOPERS
(
   STATIC_ID            varchar(50) not null unique,
   NICKNAME             varchar(500) not null,
   CATEGORY             varchar(100) not null,
   primary key (STATIC_ID)
);

/*==============================================================*/
/* Table: DEV_CHOOSEN                                           */
/*==============================================================*/
create table if not exists DEV_CHOSEN
(
   DEV_ID               varchar(50) not null,
   ORDER_ID             int not null,
   primary key (DEV_ID, ORDER_ID)
);

/*==============================================================*/
/* Table: FINISHED_ORDERS                                       */
/*==============================================================*/
create table if not exists FINISHED_ORDERS
(
   DATE_ACCEPTED        date not null,
   RATING               int not null,
   SUGGESTIONS          varchar(4200),
   FEEDBACK             varchar(4200),
   ORDER_ID             int not null,
   primary key (ORDER_ID)
);

/*==============================================================*/
/* Table: ORDERS                                                */
/*==============================================================*/
create table if not exists ORDERS
(
   ORDER_ID             int not null auto_increment,
   TICKET_ID            int not null unique,
   DATE_CREATED         datetime not null default now(),
   DATE_FINISHED        date,
   PROGRESS             int not null default 0,
   IS_PAYED             boolean not null,
   SUM                  float(8,2),
   primary key (ORDER_ID)
);

/*==============================================================*/
/* Table: TICKETS                                               */
/*==============================================================*/
create table if not exists TICKETS
(
   TICKET_ID            int not null auto_increment,
   AUTHOR               varchar(20) not null,
   CATEGORY             varchar(20) not null,
   PAYMENT_TYPE         varchar(4100),
   TEXT                 varchar(4100),
   primary key (TICKET_ID)
);

alter table CLOSED_TICKETS add constraint FK_TICKET_CLOSED foreign key (TICKET_ID)
      references TICKETS (TICKET_ID) on delete restrict on update restrict;

alter table DEV_CHOSEN add constraint FK_DEV_CHOSEN foreign key (DEV_ID)
      references DEVELOPERS (STATIC_ID) on delete restrict on update restrict;

alter table DEV_CHOSEN add constraint FK_DEV_CHOSEN2 foreign key (ORDER_ID)
      references ORDERS (ORDER_ID) on delete restrict on update restrict;

alter table FINISHED_ORDERS add constraint FK_ORDER_FINISHED foreign key (ORDER_ID)
      references ORDERS (ORDER_ID) on delete restrict on update restrict;

alter table ORDERS add constraint FK_ORDER_MADE2 foreign key (TICKET_ID)
      references TICKETS (TICKET_ID) on delete restrict on update restrict;





/*==============================================================*/
/* Table: SURVEYS                                               */
/*==============================================================*/
create table if not exists SURVEYS
(
   SURVEY_ID            int not null auto_increment,
   AUTHOR               varchar(20) not null,
   DATE_STARTED         datetime not null default now(),
   IS_ACTIVE            boolean not null default 1,
   MESSAGE_ID           varchar(20),
   SURVEY_NAME          varchar(4100) not null,
   primary key (SURVEY_ID)
);

/*==============================================================*/
/* Table: SURVEY_OPTIONS                                        */
/*==============================================================*/
create table if not exists SURVEY_OPTIONS
(
   OPTION_ID            int not null auto_increment,
   SURVEY_ID            int not null,
   OPTION_NAME          varchar(4000) not null,
   primary key (OPTION_ID)
);

/*==============================================================*/
/* Table: VOTED                                                 */
/*==============================================================*/
create table if not exists VOTED
(
   OPTION_ID            int not null,
   USER                 varchar(20) not null,
   primary key (OPTION_ID)
);

alter table SURVEY_OPTIONS add constraint FK_SURVEY_HAS_OPTION foreign key (SURVEY_ID)
      references SURVEYS (SURVEY_ID) 
      on delete cascade 
      on update restrict;

alter table VOTED add constraint FK_OPTION_VOTED foreign key (OPTION_ID)
      references SURVEY_OPTIONS (OPTION_ID) 
      on delete cascade 
      on update restrict;



/*==============================================================*/
/* Table: PRIVATE_SURVEYS                                       */
/*==============================================================*/
create table if not exists PRIVATE_SURVEYS
(
   SURVEY_ID            int not null auto_increment,
   AUTHOR               varchar(20) not null,
   DATE_STARTED         datetime not null default now(),
   IS_ACTIVE            boolean not null default 1,
   SURVEY_NAME          varchar(4100) not null,
   primary key (SURVEY_ID)
);

/*==============================================================*/
/* Table: PRIVATE_MESSAGES                                      */
/*==============================================================*/
create table if not exists PRIVATE_MESSAGES
(
   MESSAGE_ID           varchar(20) not null,
   SURVEY_ID            int not null,
   ANSWER               varchar(4200) default null,
   primary key (MESSAGE_ID)
);

alter table PRIVATE_MESSAGES add constraint FK_SURVEY_SENT foreign key (SURVEY_ID)
      references PRIVATE_SURVEYS (SURVEY_ID) 
      on delete cascade 
      on update restrict;

/*==============================================================*/
/* Table: MEMBERS                                               */
/*==============================================================*/
create table if not exists MEMBERS
(
   MEMBER_ID            varchar(20) not null,
   JOINED_AT            datetime not null default now(),
   SOURCE               varchar(200) default null,
   primary key (MEMBER_ID)
);

