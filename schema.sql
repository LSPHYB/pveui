-- pve.auth_group definition

CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- pve.auth_user definition

CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4;


-- pve.django_content_type definition

CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4;


-- pve.django_migrations definition

CREATE TABLE `django_migrations` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4;


-- pve.django_session definition

CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- pve.rbac_role definition

CREATE TABLE `rbac_role` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL,
  `code` varchar(64) NOT NULL,
  `description` varchar(256) NOT NULL,
  `data_scope` varchar(16) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `code` (`code`),
  KEY `rbac_role_code_7dbf08_idx` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4;


-- pve.audit_operationlog definition

CREATE TABLE `audit_operationlog` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `username` varchar(150) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `action_type` varchar(20) NOT NULL,
  `object_id` int(10) unsigned DEFAULT NULL,
  `object_repr` varchar(255) NOT NULL,
  `request_path` varchar(500) NOT NULL,
  `request_method` varchar(10) NOT NULL,
  `request_params` json NOT NULL,
  `ip_address` char(39) DEFAULT NULL,
  `user_agent` varchar(500) NOT NULL,
  `status_code` int(11) DEFAULT NULL,
  `error_message` longtext NOT NULL,
  `remark` varchar(255) NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `audit_operationlog_created_at_63362107` (`created_at`),
  KEY `audit_operationlog_action_type_5cfe7b6a` (`action_type`),
  KEY `audit_opera_user_id_5d9cb4_idx` (`user_id`,`created_at`),
  KEY `audit_opera_action__caf37b_idx` (`action_type`,`created_at`),
  KEY `audit_opera_content_437198_idx` (`content_type_id`,`object_id`),
  KEY `audit_opera_request_5696a5_idx` (`request_path`,`created_at`),
  KEY `audit_opera_ip_addr_9d11e0_idx` (`ip_address`,`created_at`),
  CONSTRAINT `audit_operationlog_content_type_id_0899e2db_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `audit_operationlog_user_id_f4641ac3_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6423 DEFAULT CHARSET=utf8mb4;


-- pve.auth_permission definition

CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=81 DEFAULT CHARSET=utf8mb4;


-- pve.auth_user_groups definition

CREATE TABLE `auth_user_groups` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- pve.auth_user_user_permissions definition

CREATE TABLE `auth_user_user_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- pve.django_admin_log definition

CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- pve.rbac_menu definition

CREATE TABLE `rbac_menu` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `title` varchar(64) NOT NULL,
  `path` varchar(128) NOT NULL,
  `component` varchar(128) NOT NULL,
  `icon` varchar(64) NOT NULL,
  `order` int(10) unsigned NOT NULL,
  `is_hidden` tinyint(1) NOT NULL,
  `parent_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `rbac_menu_parent__543af2_idx` (`parent_id`),
  KEY `rbac_menu_order_655075_idx` (`order`),
  CONSTRAINT `rbac_menu_parent_id_60a5b178_fk_rbac_menu_id` FOREIGN KEY (`parent_id`) REFERENCES `rbac_menu` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4;


-- pve.rbac_organization definition

CREATE TABLE `rbac_organization` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL,
  `code` varchar(64) NOT NULL,
  `order` int(10) unsigned NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `leader_id` int(11) DEFAULT NULL,
  `parent_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `rbac_organi_parent__84ac6f_idx` (`parent_id`),
  KEY `rbac_organi_order_5990b9_idx` (`order`),
  KEY `rbac_organi_code_167236_idx` (`code`),
  KEY `rbac_organization_leader_id_3d17a844_fk_auth_user_id` (`leader_id`),
  CONSTRAINT `rbac_organization_leader_id_3d17a844_fk_auth_user_id` FOREIGN KEY (`leader_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `rbac_organization_parent_id_1a868447_fk_rbac_organization_id` FOREIGN KEY (`parent_id`) REFERENCES `rbac_organization` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4;


-- pve.rbac_permission definition

CREATE TABLE `rbac_permission` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL,
  `code` varchar(64) NOT NULL,
  `http_method` varchar(6) NOT NULL,
  `url_pattern` varchar(256) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `menu_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `rbac_permis_code_f6107f_idx` (`code`),
  KEY `rbac_permis_http_me_77b18e_idx` (`http_method`),
  KEY `rbac_permission_menu_id_3dcc68be_fk_rbac_menu_id` (`menu_id`),
  CONSTRAINT `rbac_permission_menu_id_3dcc68be_fk_rbac_menu_id` FOREIGN KEY (`menu_id`) REFERENCES `rbac_menu` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=88 DEFAULT CHARSET=utf8mb4;


-- pve.rbac_role_custom_data_organizations definition

CREATE TABLE `rbac_role_custom_data_organizations` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `role_id` bigint(20) NOT NULL,
  `organization_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `rbac_role_custom_data_or_role_id_organization_id_c697e9a2_uniq` (`role_id`,`organization_id`),
  KEY `rbac_role_custom_dat_organization_id_8b71be61_fk_rbac_orga` (`organization_id`),
  CONSTRAINT `rbac_role_custom_dat_organization_id_8b71be61_fk_rbac_orga` FOREIGN KEY (`organization_id`) REFERENCES `rbac_organization` (`id`),
  CONSTRAINT `rbac_role_custom_dat_role_id_b34e6b8b_fk_rbac_role` FOREIGN KEY (`role_id`) REFERENCES `rbac_role` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4;


-- pve.rbac_role_menus definition

CREATE TABLE `rbac_role_menus` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `role_id` bigint(20) NOT NULL,
  `menu_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `rbac_role_menus_role_id_menu_id_579f5861_uniq` (`role_id`,`menu_id`),
  KEY `rbac_role_menus_menu_id_180f4f9a_fk_rbac_menu_id` (`menu_id`),
  CONSTRAINT `rbac_role_menus_menu_id_180f4f9a_fk_rbac_menu_id` FOREIGN KEY (`menu_id`) REFERENCES `rbac_menu` (`id`),
  CONSTRAINT `rbac_role_menus_role_id_323259a4_fk_rbac_role_id` FOREIGN KEY (`role_id`) REFERENCES `rbac_role` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=47 DEFAULT CHARSET=utf8mb4;


-- pve.rbac_role_permissions definition

CREATE TABLE `rbac_role_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `role_id` bigint(20) NOT NULL,
  `permission_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `rbac_role_permissions_role_id_permission_id_d01303da_uniq` (`role_id`,`permission_id`),
  KEY `rbac_role_permission_permission_id_f5e1e866_fk_rbac_perm` (`permission_id`),
  CONSTRAINT `rbac_role_permission_permission_id_f5e1e866_fk_rbac_perm` FOREIGN KEY (`permission_id`) REFERENCES `rbac_permission` (`id`),
  CONSTRAINT `rbac_role_permissions_role_id_d10416cb_fk_rbac_role_id` FOREIGN KEY (`role_id`) REFERENCES `rbac_role` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=249 DEFAULT CHARSET=utf8mb4;


-- pve.rbac_userorganization definition

CREATE TABLE `rbac_userorganization` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `is_primary` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `organization_id` bigint(20) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `rbac_userorganization_user_id_organization_id_d4132b67_uniq` (`user_id`,`organization_id`),
  KEY `rbac_useror_user_id_9f56c7_idx` (`user_id`),
  KEY `rbac_useror_organiz_cb5127_idx` (`organization_id`),
  KEY `rbac_useror_is_prim_39a0d9_idx` (`is_primary`),
  CONSTRAINT `rbac_userorganizatio_organization_id_fe119b2b_fk_rbac_orga` FOREIGN KEY (`organization_id`) REFERENCES `rbac_organization` (`id`),
  CONSTRAINT `rbac_userorganization_user_id_531ffb23_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4;


-- pve.rbac_userrole definition

CREATE TABLE `rbac_userrole` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `role_id` bigint(20) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `rbac_userrole_user_id_role_id_680dcacd_uniq` (`user_id`,`role_id`),
  KEY `rbac_userro_user_id_51c836_idx` (`user_id`),
  KEY `rbac_userro_role_id_32b7c8_idx` (`role_id`),
  CONSTRAINT `rbac_userrole_role_id_afe9516c_fk_rbac_role_id` FOREIGN KEY (`role_id`) REFERENCES `rbac_role` (`id`),
  CONSTRAINT `rbac_userrole_user_id_035f397b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4;


-- pve.system_systemsetting definition

CREATE TABLE `system_systemsetting` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_deleted` tinyint(1) NOT NULL,
  `remark` varchar(255) NOT NULL,
  `key` varchar(100) NOT NULL,
  `value` longtext NOT NULL,
  `description` varchar(255) NOT NULL,
  `category` varchar(50) NOT NULL,
  `is_encrypted` tinyint(1) NOT NULL,
  `is_public` tinyint(1) NOT NULL,
  `created_by_id` int(11) DEFAULT NULL,
  `owner_organization_id` bigint(20) DEFAULT NULL,
  `updated_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `key` (`key`),
  KEY `system_systemsetting_created_by_id_93f1f090_fk_auth_user_id` (`created_by_id`),
  KEY `system_systemsetting_owner_organization_i_b7585aa3_fk_rbac_orga` (`owner_organization_id`),
  KEY `system_systemsetting_updated_by_id_81621a23_fk_auth_user_id` (`updated_by_id`),
  KEY `system_syst_key_e923a8_idx` (`key`),
  KEY `system_syst_categor_47d80a_idx` (`category`),
  CONSTRAINT `system_systemsetting_created_by_id_93f1f090_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `system_systemsetting_owner_organization_i_b7585aa3_fk_rbac_orga` FOREIGN KEY (`owner_organization_id`) REFERENCES `rbac_organization` (`id`),
  CONSTRAINT `system_systemsetting_updated_by_id_81621a23_fk_auth_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4;


-- pve.tasks_job definition

CREATE TABLE `tasks_job` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_deleted` tinyint(1) NOT NULL,
  `remark` varchar(255) NOT NULL,
  `job_name` varchar(100) NOT NULL,
  `invoke_target` varchar(255) NOT NULL,
  `job_params` json NOT NULL,
  `cron_expression` varchar(100) NOT NULL,
  `next_valid_time` datetime(6) DEFAULT NULL,
  `status` int(11) NOT NULL,
  `job_id` varchar(128) NOT NULL,
  `last_run_at` datetime(6) DEFAULT NULL,
  `created_by_id` int(11) DEFAULT NULL,
  `owner_organization_id` bigint(20) DEFAULT NULL,
  `updated_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `job_name` (`job_name`),
  KEY `tasks_job_created_by_id_80d10384_fk_auth_user_id` (`created_by_id`),
  KEY `tasks_job_owner_organization_id_d91104aa_fk_rbac_organization_id` (`owner_organization_id`),
  KEY `tasks_job_updated_by_id_e3a97070_fk_auth_user_id` (`updated_by_id`),
  CONSTRAINT `tasks_job_created_by_id_80d10384_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `tasks_job_owner_organization_id_d91104aa_fk_rbac_organization_id` FOREIGN KEY (`owner_organization_id`) REFERENCES `rbac_organization` (`id`),
  CONSTRAINT `tasks_job_updated_by_id_e3a97070_fk_auth_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- pve.auth_group_permissions definition

CREATE TABLE `auth_group_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- pve.chat_chatmessage definition

CREATE TABLE `chat_chatmessage` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_deleted` tinyint(1) NOT NULL,
  `remark` varchar(255) NOT NULL,
  `content` longtext NOT NULL,
  `is_read` tinyint(1) NOT NULL,
  `read_at` datetime(6) DEFAULT NULL,
  `created_by_id` int(11) DEFAULT NULL,
  `owner_organization_id` bigint(20) DEFAULT NULL,
  `receiver_id` int(11) NOT NULL,
  `sender_id` int(11) NOT NULL,
  `updated_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `chat_chatmessage_created_by_id_f25b6757_fk_auth_user_id` (`created_by_id`),
  KEY `chat_chatmessage_owner_organization_i_397dce34_fk_rbac_orga` (`owner_organization_id`),
  KEY `chat_chatmessage_updated_by_id_1fcb5bd1_fk_auth_user_id` (`updated_by_id`),
  KEY `chat_chatme_sender__34ee69_idx` (`sender_id`,`receiver_id`),
  KEY `chat_chatme_receive_d79e66_idx` (`receiver_id`,`is_read`),
  KEY `chat_chatme_created_888e17_idx` (`created_at`),
  CONSTRAINT `chat_chatmessage_created_by_id_f25b6757_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `chat_chatmessage_owner_organization_i_397dce34_fk_rbac_orga` FOREIGN KEY (`owner_organization_id`) REFERENCES `rbac_organization` (`id`),
  CONSTRAINT `chat_chatmessage_receiver_id_732b2283_fk_auth_user_id` FOREIGN KEY (`receiver_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `chat_chatmessage_sender_id_80753f2b_fk_auth_user_id` FOREIGN KEY (`sender_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `chat_chatmessage_updated_by_id_1fcb5bd1_fk_auth_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- pve.pve_networktopology definition

CREATE TABLE `pve_networktopology` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_deleted` tinyint(1) NOT NULL,
  `remark` varchar(255) NOT NULL,
  `name` varchar(150) NOT NULL,
  `description` longtext NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `diagram_data` json NOT NULL,
  `metadata` json NOT NULL,
  `created_by_id` int(11) DEFAULT NULL,
  `owner_organization_id` bigint(20) DEFAULT NULL,
  `updated_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `pve_networktopology_created_by_id_d1ce4f35_fk_auth_user_id` (`created_by_id`),
  KEY `pve_networktopology_owner_organization_i_830c16b1_fk_rbac_orga` (`owner_organization_id`),
  KEY `pve_networktopology_updated_by_id_a07c22e0_fk_auth_user_id` (`updated_by_id`),
  KEY `pve_network_name_bc3e31_idx` (`name`),
  KEY `pve_network_is_acti_9b6b80_idx` (`is_active`),
  CONSTRAINT `pve_networktopology_created_by_id_d1ce4f35_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `pve_networktopology_owner_organization_i_830c16b1_fk_rbac_orga` FOREIGN KEY (`owner_organization_id`) REFERENCES `rbac_organization` (`id`),
  CONSTRAINT `pve_networktopology_updated_by_id_a07c22e0_fk_auth_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- pve.pve_pveserver definition

CREATE TABLE `pve_pveserver` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_deleted` tinyint(1) NOT NULL,
  `remark` varchar(255) NOT NULL,
  `name` varchar(100) NOT NULL,
  `host` varchar(255) NOT NULL,
  `port` int(11) NOT NULL,
  `token_id` varchar(100) NOT NULL,
  `token_secret` varchar(255) NOT NULL,
  `verify_ssl` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_by_id` int(11) DEFAULT NULL,
  `owner_organization_id` bigint(20) DEFAULT NULL,
  `updated_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `pve_pveserv_name_115cc2_idx` (`name`),
  KEY `pve_pveserv_is_acti_f1a599_idx` (`is_active`),
  KEY `pve_pveserver_created_by_id_b1e7eb93_fk_auth_user_id` (`created_by_id`),
  KEY `pve_pveserver_owner_organization_i_6a1be045_fk_rbac_orga` (`owner_organization_id`),
  KEY `pve_pveserver_updated_by_id_ca72f3fd_fk_auth_user_id` (`updated_by_id`),
  CONSTRAINT `pve_pveserver_created_by_id_b1e7eb93_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `pve_pveserver_owner_organization_i_6a1be045_fk_rbac_orga` FOREIGN KEY (`owner_organization_id`) REFERENCES `rbac_organization` (`id`),
  CONSTRAINT `pve_pveserver_updated_by_id_ca72f3fd_fk_auth_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4;


-- pve.pve_virtualmachine definition

CREATE TABLE `pve_virtualmachine` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_deleted` tinyint(1) NOT NULL,
  `remark` varchar(255) NOT NULL,
  `vmid` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `node` varchar(100) NOT NULL,
  `status` varchar(20) NOT NULL,
  `cpu_cores` int(11) NOT NULL,
  `memory_mb` int(11) NOT NULL,
  `disk_gb` int(11) NOT NULL,
  `ip_address` varchar(255) NOT NULL,
  `description` longtext NOT NULL,
  `pve_config` json NOT NULL,
  `created_by_id` int(11) DEFAULT NULL,
  `owner_organization_id` bigint(20) DEFAULT NULL,
  `server_id` bigint(20) NOT NULL,
  `updated_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `pve_virtualmachine_server_id_vmid_c85f0c1d_uniq` (`server_id`,`vmid`),
  KEY `pve_virtual_server__daf172_idx` (`server_id`,`vmid`),
  KEY `pve_virtual_status_d8360d_idx` (`status`),
  KEY `pve_virtual_node_16f17b_idx` (`node`),
  KEY `pve_virtualmachine_created_by_id_f125d88d_fk_auth_user_id` (`created_by_id`),
  KEY `pve_virtualmachine_owner_organization_i_c5c56bad_fk_rbac_orga` (`owner_organization_id`),
  KEY `pve_virtualmachine_updated_by_id_d633c870_fk_auth_user_id` (`updated_by_id`),
  CONSTRAINT `pve_virtualmachine_created_by_id_f125d88d_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `pve_virtualmachine_owner_organization_i_c5c56bad_fk_rbac_orga` FOREIGN KEY (`owner_organization_id`) REFERENCES `rbac_organization` (`id`),
  CONSTRAINT `pve_virtualmachine_server_id_a83b3571_fk_pve_pveserver_id` FOREIGN KEY (`server_id`) REFERENCES `pve_pveserver` (`id`),
  CONSTRAINT `pve_virtualmachine_updated_by_id_d633c870_fk_auth_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4;


-- pve.pve_lxccontainer definition

CREATE TABLE `pve_lxccontainer` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_deleted` tinyint(1) NOT NULL,
  `remark` varchar(255) NOT NULL,
  `vmid` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `node` varchar(100) NOT NULL,
  `status` varchar(20) NOT NULL,
  `cpu_cores` int(11) NOT NULL,
  `memory_mb` int(11) NOT NULL,
  `disk_gb` int(11) NOT NULL,
  `ip_address` varchar(255) NOT NULL,
  `description` longtext NOT NULL,
  `pve_config` json NOT NULL,
  `created_by_id` int(11) DEFAULT NULL,
  `owner_organization_id` bigint(20) DEFAULT NULL,
  `updated_by_id` int(11) DEFAULT NULL,
  `server_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `pve_lxccontainer_server_id_vmid_e672799b_uniq` (`server_id`,`vmid`),
  KEY `pve_lxccont_server__3e6979_idx` (`server_id`,`vmid`),
  KEY `pve_lxccont_status_038ad9_idx` (`status`),
  KEY `pve_lxccont_node_0b69d3_idx` (`node`),
  KEY `pve_lxccontainer_created_by_id_c580543e_fk_auth_user_id` (`created_by_id`),
  KEY `pve_lxccontainer_owner_organization_i_80372424_fk_rbac_orga` (`owner_organization_id`),
  KEY `pve_lxccontainer_updated_by_id_dc3c53c6_fk_auth_user_id` (`updated_by_id`),
  CONSTRAINT `pve_lxccontainer_created_by_id_c580543e_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `pve_lxccontainer_owner_organization_i_80372424_fk_rbac_orga` FOREIGN KEY (`owner_organization_id`) REFERENCES `rbac_organization` (`id`),
  CONSTRAINT `pve_lxccontainer_server_id_652a0d0f_fk_pve_pveserver_id` FOREIGN KEY (`server_id`) REFERENCES `pve_pveserver` (`id`),
  CONSTRAINT `pve_lxccontainer_updated_by_id_dc3c53c6_fk_auth_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4;