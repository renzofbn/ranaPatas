-- MySQL dump 10.13  Distrib 8.0.42, for Linux (x86_64)
--
-- Host: localhost    Database: tu_base_de_datos
-- ------------------------------------------------------
-- Server version	8.0.42

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `evaluaciones`
--

DROP TABLE IF EXISTS `evaluaciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `evaluaciones` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(255) NOT NULL,
  `observacion` text,
  `fecha_creada` datetime DEFAULT CURRENT_TIMESTAMP,
  `creado_por` int NOT NULL,
  `activa` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`),
  KEY `fk_evaluaciones_creado_por` (`creado_por`),
  CONSTRAINT `fk_evaluaciones_creado_por` FOREIGN KEY (`creado_por`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `eventos`
--

DROP TABLE IF EXISTS `eventos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `eventos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `fecha_creacion` datetime DEFAULT CURRENT_TIMESTAMP,
  `creado_por_usuario` varchar(50) NOT NULL,
  `id_usuario_creado` int NOT NULL,
  `lugar` varchar(150) DEFAULT NULL,
  `observaciones` text,
  `fecha_inicio` datetime DEFAULT NULL,
  `estado` varchar(50) DEFAULT 'programado',
  `torneo_empezado_en` datetime DEFAULT NULL,
  `torneo_iniciado_por` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `id_usuario_creado` (`id_usuario_creado`),
  CONSTRAINT `eventos_ibfk_1` FOREIGN KEY (`id_usuario_creado`) REFERENCES `usuarios` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `invalidaciones_sesion`
--

DROP TABLE IF EXISTS `invalidaciones_sesion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `invalidaciones_sesion` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `motivo` enum('cambio_password','eliminacion_usuario','logout_manual','admin_action') NOT NULL,
  `fecha_invalidacion` datetime DEFAULT CURRENT_TIMESTAMP,
  `invalidado_por` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  KEY `invalidado_por` (`invalidado_por`),
  CONSTRAINT `invalidaciones_sesion_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE,
  CONSTRAINT `invalidaciones_sesion_ibfk_2` FOREIGN KEY (`invalidado_por`) REFERENCES `usuarios` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notificaciones_admin`
--

DROP TABLE IF EXISTS `notificaciones_admin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notificaciones_admin` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tipo` varchar(50) NOT NULL,
  `titulo` varchar(200) NOT NULL,
  `mensaje` text NOT NULL,
  `usuario_relacionado` int DEFAULT NULL,
  `leida` tinyint(1) DEFAULT '0',
  `fecha_creacion` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `usuario_relacionado` (`usuario_relacionado`),
  CONSTRAINT `notificaciones_admin_ibfk_1` FOREIGN KEY (`usuario_relacionado`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `participante_evaluacion`
--

DROP TABLE IF EXISTS `participante_evaluacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `participante_evaluacion` (
  `id` int NOT NULL AUTO_INCREMENT,
  `evaluacion_id` int NOT NULL,
  `usuario_id` int NOT NULL,
  `fecha_agregacion` datetime DEFAULT CURRENT_TIMESTAMP,
  `agregado_por` int NOT NULL,
  `tiempo_inicio` datetime DEFAULT NULL,
  `tiempo_final` datetime DEFAULT NULL,
  `iniciado_por` int DEFAULT NULL,
  `terminado_por` int DEFAULT NULL,
  `observaciones` text,
  `estado` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_participante_evaluacion_usuario` (`usuario_id`),
  KEY `fk_participante_evaluacion_agregado_por` (`agregado_por`),
  KEY `fk_participante_evaluacion_iniciado_por` (`iniciado_por`),
  KEY `fk_participante_evaluacion_terminado_por` (`terminado_por`),
  KEY `fk_participante_evaluacion_evaluacion_temp` (`evaluacion_id`),
  CONSTRAINT `fk_participante_evaluacion_agregado_por_temp` FOREIGN KEY (`agregado_por`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_participante_evaluacion_evaluacion_temp` FOREIGN KEY (`evaluacion_id`) REFERENCES `evaluaciones` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_participante_evaluacion_iniciado_por_temp` FOREIGN KEY (`iniciado_por`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_participante_evaluacion_terminado_por_temp` FOREIGN KEY (`terminado_por`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_participante_evaluacion_usuario_temp` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `participantes_evento`
--

DROP TABLE IF EXISTS `participantes_evento`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `participantes_evento` (
  `id` int NOT NULL AUTO_INCREMENT,
  `codigo` varchar(50) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `tiempo_inicio` datetime DEFAULT NULL,
  `tiempo_llegada` datetime DEFAULT NULL,
  `tiempo_total` time DEFAULT NULL,
  `tiempo_iniciado_por` int DEFAULT NULL,
  `tiempo_terminado_por` int DEFAULT NULL,
  `participante_agregado_por` int NOT NULL,
  `evento_id` int NOT NULL,
  `usuario_agregado_en` datetime DEFAULT CURRENT_TIMESTAMP,
  `detalles` text,
  `usuario_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_usuario_evento` (`evento_id`,`usuario_id`),
  KEY `tiempo_iniciado_por` (`tiempo_iniciado_por`),
  KEY `tiempo_terminado_por` (`tiempo_terminado_por`),
  KEY `participante_agregado_por` (`participante_agregado_por`),
  KEY `idx_participante_usuario` (`usuario_id`),
  CONSTRAINT `participantes_evento_ibfk_1` FOREIGN KEY (`tiempo_iniciado_por`) REFERENCES `usuarios` (`id`),
  CONSTRAINT `participantes_evento_ibfk_2` FOREIGN KEY (`tiempo_terminado_por`) REFERENCES `usuarios` (`id`),
  CONSTRAINT `participantes_evento_ibfk_3` FOREIGN KEY (`participante_agregado_por`) REFERENCES `usuarios` (`id`),
  CONSTRAINT `participantes_evento_ibfk_4` FOREIGN KEY (`evento_id`) REFERENCES `eventos` (`id`),
  CONSTRAINT `participantes_evento_ibfk_5` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles` (
  `id` int NOT NULL,
  `nombre` varchar(50) NOT NULL,
  `descripcion` text,
  `permisos` text COMMENT 'JSON con permisos específicos',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sesiones`
--

DROP TABLE IF EXISTS `sesiones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sesiones` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `token` varchar(255) NOT NULL,
  `fecha_creacion` datetime DEFAULT CURRENT_TIMESTAMP,
  `fecha_expiracion` datetime NOT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` text,
  `activa` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `token` (`token`),
  KEY `idx_token` (`token`),
  KEY `idx_usuario_activa` (`usuario_id`,`activa`),
  CONSTRAINT `sesiones_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `usuario` varchar(50) NOT NULL,
  `correo` varchar(100) NOT NULL,
  `contrasena` varchar(255) NOT NULL,
  `isAdmin` tinyint(1) DEFAULT '0',
  `ultimo_login` datetime DEFAULT NULL,
  `password_cambiado_en` datetime DEFAULT NULL,
  `cuenta_bloqueada` tinyint(1) DEFAULT '0',
  `intentos_fallidos` int DEFAULT '0',
  `bloqueado_hasta` datetime DEFAULT NULL,
  `fecha_registro` datetime DEFAULT CURRENT_TIMESTAMP,
  `estado_aprobacion` enum('pendiente','aprobado','rechazado') DEFAULT 'pendiente',
  `fecha_aprobacion` datetime DEFAULT NULL,
  `aprobado_por` int DEFAULT NULL,
  `observaciones_admin` text,
  `rol` int DEFAULT '1' COMMENT '1=Participante, 2=Organizador, 3=Admin',
  PRIMARY KEY (`id`),
  UNIQUE KEY `usuario` (`usuario`),
  UNIQUE KEY `correo` (`correo`),
  KEY `idx_usuarios_nombre` (`nombre`),
  KEY `fk_usuarios_aprobado_por` (`aprobado_por`),
  KEY `idx_usuarios_estado_aprobacion` (`estado_aprobacion`),
  KEY `idx_usuarios_rol` (`rol`),
  CONSTRAINT `fk_usuarios_aprobado_por` FOREIGN KEY (`aprobado_por`) REFERENCES `usuarios` (`id`),
  CONSTRAINT `fk_usuarios_rol` FOREIGN KEY (`rol`) REFERENCES `roles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-07-09 17:00:17
