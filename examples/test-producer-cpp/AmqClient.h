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


#include <decaf/lang/Thread.h>
#include <decaf/lang/Runnable.h>
#include <decaf/util/concurrent/CountDownLatch.h>
#include <decaf/lang/Long.h>
#include <decaf/util/Date.h>
#include <activemq/core/ActiveMQConnectionFactory.h>
#include <activemq/util/Config.h>
#include <activemq/library/ActiveMQCPP.h>
#include <cms/Connection.h>
#include <cms/Session.h>
#include <cms/TextMessage.h>
#include <cms/BytesMessage.h>
#include <cms/MapMessage.h>
#include <cms/ExceptionListener.h>
#include <cms/MessageListener.h>
#include <string>
#include "RunInfo.h"

namespace Adara
{
namespace Utils
{

class AmqClient
{

protected:
   std::string m_brokerUri;
   std::string m_user;
   std::string m_pass;
   std::auto_ptr<cms::Connection> m_connection;
   std::auto_ptr<cms::ConnectionFactory> m_connectionFactory;
   std::auto_ptr<cms::Session> m_session;
   std::auto_ptr<cms::Destination> m_destination;
   bool m_connected;


public:

   AmqClient( const std::string& brokerUri, const std::string& user, const std::string& pass);
   ~AmqClient();

   /// @brief sends the run info message to the Queue by name
   /// @return true if message was sent successfully
   bool send(const std::string& queueName, const RunInfo& ri);

   /// @todo implement a receive if needed

protected:
   /// @brief connects to the broker
   void connect();


};


}
}

