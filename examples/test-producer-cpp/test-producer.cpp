// ****************************************************************************
//
/// @filename: test-producer.cpp
///
///  @author: D. Reitz
///
///  @date: 19-Sept-2012
///
///  @summary: Example C++ test using the AmqClient 
/// 
// *****************************************************************************

#include "AmqClient.h"
int main (void)
{
   std::string uri = "failover://(tcp://heidelberg:61616,tcp://drembpro-vnet:61616)?randomize=true";
   Adara::Utils::RunInfo ri("IPTS-5678", "HYSA", 9999, "the-file-name"); 
   Adara::Utils::AmqClient amqc(uri, "icat", "icat");
   amqc.send("TRANSLATION.STARTED", ri);
   amqc.send("TRANSLATION.FINISHED", ri);
   amqc.send("CATALOG.DATA_READY", ri);

  return 0;
}
