// ****************************************************************************
//
///  @filename: AmqClient.h
///
///  @author: D. Reitz
///
///  @date: 19-Sept-2012
///
///  @summary: C++ ActiveMQ client for use in ADARA 
/// 
// *****************************************************************************

#include "AmqClient.h"

namespace Adara
{
namespace Utils
{

AmqClient::AmqClient( const std::string& brokerUri, const std::string& user, const std::string& pass)
: m_brokerUri(brokerUri),
  m_user(user),
  m_pass(pass),
  m_connectionFactory(NULL),
  m_connection(NULL),
  m_session(NULL),
  m_connected(false)
{
   activemq::library::ActiveMQCPP::initializeLibrary();
   connect();
}

AmqClient::~AmqClient() {}

/// @brief sends the text message to the Queue by name
/// @return true if messsage was sent successfully
bool AmqClient::send(const std::string& queueName, const Adara::Utils::RunInfo& ri)
{
   bool retval (false);
   if(!m_connected) connect();
   
   //std::cout << "Creating queue \n" << std::flush;
   std::auto_ptr<cms::Queue>q(m_session->createQueue(queueName));

   // Now make a message producer
   //std::cout << "Creating producer \n" << std::flush;
   std::auto_ptr<cms::MessageProducer> producer(m_session->createProducer(q.get()));

   // Now create a TextMessage
   //std::cout << "Creating message \n" << std::flush;
   std::auto_ptr<cms::TextMessage> textm( m_session->createTextMessage() );

   // Set the payload
   //std::cout << "Setting the text payload \n" << std::flush;
   textm->setText( ri.getDict());

   //std::cout << "Sending the message.\n" << std::flush;
   producer->send(textm.get());

   //std::cout << "Sent the message.\n" << std::flush;
   retval = true;
   return retval;

}

void AmqClient::connect()
{
   m_connectionFactory.reset(cms::ConnectionFactory::createCMSConnectionFactory(m_brokerUri)),
   m_connection.reset(m_connectionFactory->createConnection(m_user, m_pass)),
   m_session.reset(m_connection->createSession()),
   m_connection->start();
   m_connected = true;
}

}
}

